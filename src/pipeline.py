"""
E-V-W Evaluation Stack 主流程编排
"""

import json
from pathlib import Path
from typing import Dict, List
from .data.data_loader import DataLoader
from .agents.extraction_agent import ExtractionAgent
from .agents.verification_agent import VerificationAgent
from .agents.weighting_agent import WeightingAgent
from .agents.synthesis_agent import SynthesisAgent
from .utils.llm_client import LLMClient
from .utils.rag import SimpleRAG
from .utils.embedding_rag import EmbeddingRAG
from .utils.hybrid_rag import HybridRAG
from .utils.reranking_rag import RerankingRAG
import yaml


class EVWPipeline:
    """E-V-W 评估流程"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化流程"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {e}")
        
        if not self.config:
            raise ValueError("配置文件为空")
        
        # 初始化组件
        self.data_loader = DataLoader()
        
        # 从 config 读取 API key（如果存在）
        llm_config = self.config.get('llm', {})
        api_key = llm_config.get('api_key')
        if api_key == "":
            api_key = None  # 空字符串视为未设置
        
        self.llm_client = LLMClient(
            provider=llm_config.get('provider', 'openai'),
            api_key=api_key,
            model=llm_config.get('model', 'gpt-4'),
            temperature=llm_config.get('temperature', 0.3),
            base_url=llm_config.get('base_url')  # 支持自定义 base_url（如 DeepSeek）
        )
        self.extraction_agent = ExtractionAgent(self.llm_client)
        
        # 初始化 RAG 和 Verification Agent
        rag_config = self.config.get('rag', {})
        rag_method = rag_config.get('method', 'simple')  # 'simple', 'embedding', 或 'hybrid'
        use_reranking = rag_config.get('use_reranking', False)  # 是否启用重排序
        
        if rag_method == 'hybrid':
            # 使用混合 RAG（结合关键词和语义检索）
            embedding_model = rag_config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
            keyword_weight = rag_config.get('keyword_weight', 0.3)
            semantic_weight = rag_config.get('semantic_weight', 0.7)
            base_rag = HybridRAG(
                keyword_weight=keyword_weight,
                semantic_weight=semantic_weight,
                embedding_model=embedding_model,
                chunk_size=rag_config.get('chunk_size', 500),
                chunk_overlap=rag_config.get('chunk_overlap', 50)
            )
            print(f"[INFO] Using Hybrid RAG (keyword: {keyword_weight}, semantic: {semantic_weight})")
        elif rag_method == 'embedding':
            # 使用基于 Embedding 的 RAG
            embedding_model = rag_config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
            base_rag = EmbeddingRAG(
                model_name=embedding_model,
                chunk_size=rag_config.get('chunk_size', 500),
                chunk_overlap=rag_config.get('chunk_overlap', 50)
            )
            print(f"[INFO] Using Embedding RAG with model: {embedding_model}")
        else:
            # 使用简单的关键词匹配 RAG
            base_rag = SimpleRAG(
                chunk_size=rag_config.get('chunk_size', 500),
                chunk_overlap=rag_config.get('chunk_overlap', 50)
            )
            print(f"[INFO] Using Simple RAG (keyword-based)")
        
        # 如果启用重排序，包装基础 RAG
        if use_reranking:
            reranker_model = rag_config.get('reranker_model', 'cross-encoder/ms-marco-MiniLM-L-6-v2')
            initial_top_k = rag_config.get('reranking_initial_top_k', 20)
            rag = RerankingRAG(
                base_rag=base_rag,
                reranker_model=reranker_model,
                initial_top_k=initial_top_k,
                use_reranking=True
            )
            print(f"[INFO] Reranking enabled with model: {reranker_model}")
        else:
            rag = base_rag
        
        self.rag = rag  # 保存引用以便后续使用
        self.verification_agent = VerificationAgent(self.llm_client, rag)
        
        # 初始化 Weighting Agent
        weighting_config = self.config.get('weighting', {})
        self.weighting_agent = WeightingAgent(
            alpha=weighting_config.get('alpha', 0.5),
            beta=weighting_config.get('beta', 0.5)
        )
        
        # 初始化 Synthesis Agent
        synthesis_config = self.config.get('synthesis', {})
        self.synthesis_agent = SynthesisAgent(
            accept_threshold=synthesis_config.get('accept_threshold', 0.6),
            topics=synthesis_config.get('topics', ["Novelty", "Experiments", "Writing", "Significance", "Reproducibility"]),
            use_10_point_scale=synthesis_config.get('use_10_point_scale', True)  # 默认使用10分制
        )
    
    def step1_extraction(self, paper_id: str) -> List[Dict]:
        """
        Step 1: 结构化提取
        
        Args:
            paper_id: 论文 ID
            
        Returns:
            提取的观点列表
        """
        print(f"[Step 1] Starting claim extraction for paper {paper_id}...")
        
        # 加载 reviews
        reviews = self.data_loader.load_reviews(paper_id)
        if not reviews:
            print(f"[WARNING] No reviews found for paper {paper_id}")
            return []
        
        # 提取观点
        claims = self.extraction_agent.process_reviews(reviews)
        
        # 保存结果
        self.data_loader.save_claims(paper_id, claims)
        
        print(f"[Step 1] Completed: Extracted {len(claims)} claims")
        return claims
    
    def step2_verification(self, paper_id: str) -> Dict[str, Dict]:
        """
        Step 2: 事实验证
        
        Args:
            paper_id: 论文 ID
            
        Returns:
            验证结果字典，key 为 claim_id
        """
        print(f"[Step 2] Starting verification for paper {paper_id}...")
        
        # 1. 加载 claims
        claims = self.data_loader.load_claims(paper_id)
        if not claims:
            print(f"[WARNING] No claims found for paper {paper_id}. Please run Step 1 first.")
            return {}
        
        # 2. 加载论文文本
        try:
            paper_text = self.data_loader.load_paper_text(paper_id)
        except Exception as e:
            print(f"[ERROR] Failed to load paper text: {e}")
            return {}
        
        # 2.3. 提取论文sections（用于section过滤）
        from .data.pdf_parser import PDFParser
        pdf_parser = PDFParser()
        paper_sections = pdf_parser.extract_sections(paper_text)
        if paper_sections:
            # 只打印section数量，避免编码问题
            section_names = [name[:50] for name in list(paper_sections.keys())[:10]]  # 只显示前10个，截断长名称
            print(f"[INFO] Extracted {len(paper_sections)} sections")
        
        # 2.5. 如果是 Embedding RAG 或 Hybrid RAG，构建或加载索引
        if isinstance(self.rag, EmbeddingRAG) or isinstance(self.rag, HybridRAG):
            rag_config = self.config.get('rag', {})
            index_path = rag_config.get('index_path')
            use_cache = rag_config.get('use_cache', True)
            
            # 获取实际的语义 RAG 对象（HybridRAG 内部包含 semantic_rag）
            semantic_rag = self.rag
            if isinstance(self.rag, HybridRAG):
                semantic_rag = self.rag.semantic_rag
            
            if index_path and use_cache:
                # 尝试加载已保存的索引
                paper_index_path = f"{index_path}/{paper_id}"
                try:
                    if Path(f"{paper_index_path}.index").exists():
                        print(f"[RAG] Loading cached index for {paper_id}...")
                        semantic_rag.load_index(paper_index_path)
                    else:
                        print(f"[RAG] Building new index for {paper_id}...")
                        semantic_rag.build_index(paper_text, save_path=paper_index_path, paper_sections=paper_sections)
                except Exception as e:
                    print(f"[WARNING] Failed to load/save index: {e}, building in memory...")
                    semantic_rag.build_index(paper_text, paper_sections=paper_sections)
            else:
                # 在内存中构建索引（不保存）
                if not semantic_rag.is_built():
                    print(f"[RAG] Building index for {paper_id}...")
                    semantic_rag.build_index(paper_text, paper_sections=paper_sections)
        
        # 3. 对每个有证据的 claim 进行验证（传递sections用于section过滤）
        verifications = self.verification_agent.process_claims(claims, paper_text, paper_sections)
        
        # 4. 保存验证结果
        verifications_path = self.data_loader.base_path / "results" / "verifications" / f"{paper_id}_verified.json"
        verifications_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(verifications_path, 'w', encoding='utf-8') as f:
            json.dump(verifications, f, ensure_ascii=False, indent=2)
        
        # 转换为字典格式
        verification_dict = {v['id']: v for v in verifications}
        
        print(f"[Step 2] Completed. Verified {len(verifications)} claims.")
        
        # 显示统计信息
        if verifications:
            true_count = sum(1 for v in verifications if v['verification_result'] == 'True')
            false_count = sum(1 for v in verifications if v['verification_result'] == 'False')
            partial_count = sum(1 for v in verifications if v['verification_result'] == 'Partially_True')
            print(f"  - True: {true_count}, False: {false_count}, Partially_True: {partial_count}")
        
        return verification_dict
    
    def step3_weighting(self, paper_id: str) -> Dict[str, Dict]:
        """
        Step 3: Bias Calculation & Weighting
        
        Args:
            paper_id: 论文 ID
            
        Returns:
            权重字典，包含每个 reviewer 的权重和详细指标
        """
        print(f"[Step 3] Starting weight calculation for paper {paper_id}...")
        
        # 1. 加载 claims 和 verifications
        claims = self.data_loader.load_claims(paper_id)
        if not claims:
            print(f"[WARNING] No claims found for paper {paper_id}. Please run Step 1 first.")
            return {}
        
        verifications = self.data_loader.load_verifications(paper_id)
        if not verifications:
            print(f"[WARNING] No verifications found for paper {paper_id}. Please run Step 2 first.")
            return {}
        
        # 2. 计算每个 reviewer 的权重
        weights = self.weighting_agent.process_all_reviewers(claims, verifications)
        
        # 3. 保存权重结果
        weights_path = self.data_loader.base_path / "results" / "weights" / f"{paper_id}_weights.json"
        weights_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(weights_path, 'w', encoding='utf-8') as f:
            json.dump(weights, f, ensure_ascii=False, indent=2)
        
        print(f"[Step 3] Completed. Calculated weights for {len(weights)} reviewers.")
        
        # 显示统计信息
        if weights:
            print(f"\n[Statistics] Reviewer Weights:")
            for reviewer_id, data in sorted(weights.items()):
                print(f"  - {reviewer_id}:")
                print(f"    Weight: {data['weight']:.3f}")
                print(f"    Hollowness: {data['hollowness']:.3f} ({data['num_claims'] - data['num_claims_with_evidence']}/{data['num_claims']} claims without evidence)")
                print(f"    Hallucination: {data['hallucination']:.3f} ({data['num_false_claims']}/{data['num_claims_with_evidence']} false claims)")
                print(f"    Total claims: {data['num_claims']}")
        
        return weights
    
    def step4_synthesis(self, paper_id: str) -> str:
        """
        Step 4: Meta-Review Synthesis
        
        Args:
            paper_id: 论文 ID
            
        Returns:
            生成的报告文本
        """
        print(f"[Step 4] Starting synthesis for paper {paper_id}...")
        
        # 1. 加载所有数据
        claims = self.data_loader.load_claims(paper_id)
        if not claims:
            print(f"[WARNING] No claims found for paper {paper_id}. Please run Step 1 first.")
            return ""
        
        verifications = self.data_loader.load_verifications(paper_id)
        if not verifications:
            print(f"[WARNING] No verifications found for paper {paper_id}. Please run Step 2 first.")
            return ""
        
        weights = self.data_loader.load_weights(paper_id)
        if not weights:
            print(f"[WARNING] No weights found for paper {paper_id}. Please run Step 3 first.")
            return ""
        
        # 2. 生成报告
        report = self.synthesis_agent.generate_report(paper_id, claims, verifications, weights)
        
        # 3. 保存报告
        report_path = self.data_loader.base_path / "results" / "synthesis" / f"{paper_id}_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"[Step 4] Completed. Report saved to: {report_path}")
        
        return report
    
    def run_pipeline(self, paper_id: str):
        """
        运行完整的 E-V-W 流程
        
        Args:
            paper_id: 论文 ID
        """
        print(f"\n{'='*60}")
        print(f"开始处理论文: {paper_id}")
        print(f"{'='*60}\n")
        
        # Step 1: 提取
        claims = self.step1_extraction(paper_id)
        
        # Step 2: 验证
        verifications = self.step2_verification(paper_id)
        
        # Step 3: 加权
        weights = self.step3_weighting(paper_id)
        
        # Step 4: 合成
        report = self.step4_synthesis(paper_id)
        
        print(f"\n{'='*60}")
        print(f"论文 {paper_id} 处理完成")
        print(f"{'='*60}\n")
        
        return {
            'claims': claims,
            'verifications': verifications,
            'weights': weights,
            'report': report
        }


if __name__ == "__main__":
    pipeline = EVWPipeline()
    # 示例：处理论文
    # pipeline.run_pipeline("paper_001")

