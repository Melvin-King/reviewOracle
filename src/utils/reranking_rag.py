"""
重排序 RAG 实现
使用 Cross-Encoder 对初步检索结果进行重排序，提高检索精度
"""

from typing import List, Tuple, Optional, Dict, Union
from sentence_transformers import CrossEncoder


class RerankingRAG:
    """
    重排序 RAG：对初步检索结果使用 Cross-Encoder 进行重排序
    
    工作流程：
    1. 使用基础 RAG 进行初步检索（返回更多候选，如 top_k=20）
    2. 使用 Cross-Encoder 对候选结果进行重排序
    3. 返回重排序后的 top_k 个结果
    """
    
    def __init__(self, 
                 base_rag,
                 reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
                 initial_top_k: int = 20,
                 use_reranking: bool = True):
        """
        Args:
            base_rag: 基础 RAG 实例（SimpleRAG, EmbeddingRAG, 或 HybridRAG）
            reranker_model: Cross-Encoder 模型名称
            initial_top_k: 初步检索返回的候选数量（重排序前）
            use_reranking: 是否启用重排序（如果为False，直接使用基础RAG的结果）
        """
        self.base_rag = base_rag
        self.initial_top_k = initial_top_k
        self.use_reranking = use_reranking
        
        if use_reranking:
            print(f"[RerankingRAG] Loading reranker model: {reranker_model}")
            try:
                self.reranker = CrossEncoder(reranker_model)
                print(f"[RerankingRAG] Reranker loaded successfully")
            except Exception as e:
                print(f"[WARNING] Failed to load reranker: {e}, disabling reranking")
                self.use_reranking = False
                self.reranker = None
        else:
            self.reranker = None
    
    def retrieve_relevant_chunks(self, 
                                paper_text: Optional[str] = None,
                                query: str = "",
                                top_k: int = 5,
                                target_section: Optional[str] = None,
                                paper_sections: Optional[Dict[str, str]] = None) -> List[Tuple[str, float]]:
        """
        检索相关文本块（带重排序）
        
        Args:
            paper_text: 论文文本（SimpleRAG 和 HybridRAG 需要，EmbeddingRAG 不需要）
            query: 查询文本
            top_k: 返回前 k 个最相关的块
            target_section: 目标section名称（如果指定，只在该section中检索）
            paper_sections: 论文的section字典
            
        Returns:
            (文本块, 重排序分数) 的列表，按分数降序排列
        """
        # 1. 初步检索（返回更多候选）
        from ..utils.embedding_rag import EmbeddingRAG
        from ..utils.hybrid_rag import HybridRAG
        
        try:
            if isinstance(self.base_rag, HybridRAG):
                # Hybrid RAG: 需要 paper_text
                if paper_text is None:
                    raise ValueError("HybridRAG requires paper_text parameter")
                candidates = self.base_rag.retrieve_relevant_chunks(
                    paper_text, query, top_k=self.initial_top_k,
                    target_section=target_section, paper_sections=paper_sections
                )
            elif isinstance(self.base_rag, EmbeddingRAG):
                # Embedding RAG: 不需要 paper_text（已构建索引）
                candidates = self.base_rag.retrieve_relevant_chunks(
                    query, top_k=self.initial_top_k, target_section=target_section
                )
            else:
                # Simple RAG: 需要 paper_text
                if paper_text is None:
                    raise ValueError("SimpleRAG requires paper_text parameter")
                candidates = self.base_rag.retrieve_relevant_chunks(
                    paper_text, query, top_k=self.initial_top_k,
                    target_section=target_section, paper_sections=paper_sections
                )
        except Exception as e:
            print(f"[ERROR] Base RAG retrieval failed: {e}")
            return []
        
        if not candidates:
            return []
        
        # 如果不需要重排序或没有reranker，直接返回top_k
        if not self.use_reranking or self.reranker is None:
            return candidates[:top_k]
        
        # 2. 使用 Cross-Encoder 重排序
        # 准备查询-文本对
        pairs = [[query, chunk] for chunk, _ in candidates]
        
        # 计算重排序分数
        try:
            rerank_scores = self.reranker.predict(pairs)
        except Exception as e:
            print(f"[WARNING] Reranking failed: {e}, using original scores")
            return candidates[:top_k]
        
        # 3. 合并原始分数和重排序分数（可选：可以只使用重排序分数）
        # 这里我们使用重排序分数，因为它更准确
        reranked_results = []
        for (chunk, original_score), rerank_score in zip(candidates, rerank_scores):
            # 将重排序分数归一化到 [0, 1]（CrossEncoder 输出可能是任意范围）
            # 通常 CrossEncoder 输出已经是相关性分数，可以直接使用
            normalized_score = float(rerank_score)
            reranked_results.append((chunk, normalized_score))
        
        # 4. 按重排序分数排序
        reranked_results.sort(key=lambda x: x[1], reverse=True)
        
        # 5. 返回 top_k
        return reranked_results[:top_k]
    
    def get_context(self,
                    paper_text: Optional[str] = None,
                    query: str = "",
                    top_k: int = 5,
                    target_section: Optional[str] = None,
                    paper_sections: Optional[Dict[str, str]] = None) -> str:
        """
        获取与查询相关的上下文（合并多个块）
        
        Args:
            paper_text: 论文文本（SimpleRAG 和 HybridRAG 需要，EmbeddingRAG 不需要）
            query: 查询文本
            top_k: 返回前 k 个最相关的块
            target_section: 目标section名称
            paper_sections: 论文的section字典
            
        Returns:
            合并后的上下文文本
        """
        # 直接使用retrieve_relevant_chunks，它会根据base_rag类型自动处理
        chunks = self.retrieve_relevant_chunks(
            paper_text, query, top_k, target_section, paper_sections
        )
        
        if not chunks:
            return ""
        
        # 合并前 k 个块
        context_parts = [chunk for chunk, score in chunks]
        return "\n\n".join(context_parts)
    
    def build_index(self, paper_text: str, save_path: Optional[str] = None, paper_sections: Optional[Dict[str, str]] = None):
        """
        构建索引（委托给基础 RAG）
        
        Args:
            paper_text: 论文文本
            save_path: 索引保存路径
            paper_sections: 论文的section字典
        """
        from ..utils.embedding_rag import EmbeddingRAG
        from ..utils.hybrid_rag import HybridRAG
        
        if isinstance(self.base_rag, (EmbeddingRAG, HybridRAG)):
            self.base_rag.build_index(paper_text, save_path, paper_sections)
    
    def load_index(self, load_path: str):
        """加载索引（委托给基础 RAG）"""
        from ..utils.embedding_rag import EmbeddingRAG
        from ..utils.hybrid_rag import HybridRAG
        
        if isinstance(self.base_rag, (EmbeddingRAG, HybridRAG)):
            self.base_rag.load_index(load_path)
    
    def is_built(self) -> bool:
        """检查索引是否已构建"""
        from ..utils.embedding_rag import EmbeddingRAG
        from ..utils.hybrid_rag import HybridRAG
        
        if isinstance(self.base_rag, (EmbeddingRAG, HybridRAG)):
            return self.base_rag.is_built()
        return True  # SimpleRAG 不需要构建索引

