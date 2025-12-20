"""
Step 2: Fact Verification Agent (事实验证层)
验证观点是否与论文事实一致
"""

import json
import re
import sys
import io
from typing import List, Dict, Optional
from ..utils.llm_client import LLMClient
from ..utils.rag import SimpleRAG

# 设置UTF-8编码输出（Windows兼容）
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass


class VerificationAgent:
    """事实验证 Agent"""
    
    def __init__(self, llm_client: LLMClient, rag: Optional[SimpleRAG] = None):
        """
        Args:
            llm_client: LLM 客户端
            rag: RAG 工具，如果为 None 则创建默认实例
        """
        self.llm = llm_client
        self.rag = rag or SimpleRAG(chunk_size=500, chunk_overlap=50)
        
        self.system_prompt = """You are a fact-checking expert for academic papers. Your task is to verify whether a reviewer's claim about a paper is consistent with the actual content of the paper.

For each claim, you need to determine:
1. verification_result: One of "True", "False", or "Partially_True"
   - True: The claim is fully supported by the paper
   - False: The claim contradicts or is not supported by the paper
   - Partially_True: The claim is partially correct but has some inaccuracies
2. verification_reason: A clear explanation of why you reached this conclusion, citing specific evidence from the paper
3. confidence: A confidence score between 0.0 and 1.0

You must base your judgment solely on the evidence provided from the paper. Be objective and precise."""
        
        # Section关键词映射：用于识别claim相关的section
        self.section_keywords = {
            'experiments': ['experiment', 'experimental', 'evaluation', 'dataset', 'baseline', 'metric', 'result'],
            'results': ['result', 'finding', 'performance', 'accuracy', 'score', 'improvement'],
            'methodology': ['method', 'methodology', 'approach', 'algorithm', 'model', 'architecture', 'design'],
            'method': ['method', 'methodology', 'approach', 'algorithm', 'model', 'architecture', 'design'],
            'introduction': ['introduction', 'motivation', 'background', 'problem'],
            'related work': ['related work', 'related', 'previous', 'prior work', 'literature'],
            'discussion': ['discussion', 'analysis', 'interpretation', 'implication'],
            'conclusion': ['conclusion', 'summary', 'future work']
        }
    
    def identify_relevant_section(self, claim: Dict, available_sections: List[str] = None) -> Optional[str]:
        """
        识别claim相关的论文section
        
        Args:
            claim: 观点字典，包含 statement, substantiation_content, topic 等
            available_sections: 论文中可用的section列表（可选，用于精确匹配）
            
        Returns:
            相关的section名称，如果无法识别则返回None
        """
        # 获取claim的文本内容
        statement = claim.get('statement', '').lower()
        substantiation = claim.get('substantiation_content', '').lower()
        topic = claim.get('topic', '').lower()
        
        # 合并所有文本用于匹配
        claim_text = f"{statement} {substantiation} {topic}"
        
        # 1. 首先检查topic字段（如果存在）
        if topic:
            topic_to_section = {
                'experiments': 'experiments',
                'experimental': 'experiments',
                'methodology': 'methodology',
                'method': 'method',
                'results': 'results',
                'result': 'results'
            }
            for key, section in topic_to_section.items():
                if key in topic:
                    if available_sections:
                        # 尝试在可用sections中找到匹配的
                        for avail_sec in available_sections:
                            if section.lower() in avail_sec.lower() or avail_sec.lower() in section.lower():
                                return avail_sec
                    return section
        
        # 2. 基于关键词匹配
        best_match = None
        best_score = 0
        
        for section_name, keywords in self.section_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in claim_text:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = section_name
        
        # 3. 如果找到了匹配，尝试在available_sections中精确匹配
        if best_match and available_sections:
            for avail_sec in available_sections:
                avail_sec_lower = avail_sec.lower()
                if best_match in avail_sec_lower or avail_sec_lower in best_match:
                    return avail_sec
            # 如果找不到精确匹配，返回best_match（可能需要在后续处理中标准化）
            return best_match
        
        return best_match if best_score > 0 else None
    
    def verify_claim(self, claim: Dict, paper_text: str = None, paper_sections: Dict[str, str] = None) -> Dict:
        """
        验证单个观点
        
        Args:
            claim: 观点字典，包含 id, statement, substantiation_content 等
            paper_text: 论文文本
            paper_sections: 论文的section字典，key为section名，value为section内容
            
        Returns:
            验证结果字典，包含 id, verification_result, verification_reason, confidence
        """
        claim_id = claim.get('id', '')
        statement = claim.get('statement', '')
        substantiation_content = claim.get('substantiation_content', '')
        
        # 构建查询：结合 statement 和 substantiation
        query = f"{statement}"
        if substantiation_content:
            query += f" {substantiation_content}"
        
        # 识别相关的section
        target_section = None
        if paper_sections:
            available_sections = list(paper_sections.keys())
            target_section = self.identify_relevant_section(claim, available_sections)
            if target_section:
                # 截断section名称以避免编码问题
                section_display = target_section[:50] if len(target_section) > 50 else target_section
                print(f"    [Section Filter] Claim {claim_id} -> Section: {section_display}")
        
        # 使用 RAG 检索相关段落（支持section过滤）
        # 检查 RAG 类型以使用正确的接口
        from ..utils.embedding_rag import EmbeddingRAG
        from ..utils.hybrid_rag import HybridRAG
        from ..utils.reranking_rag import RerankingRAG
        
        # 如果使用RerankingRAG，需要检查其base_rag类型
        if isinstance(self.rag, RerankingRAG):
            # RerankingRAG: 根据base_rag类型决定参数
            if isinstance(self.rag.base_rag, EmbeddingRAG):
                context = self.rag.get_context(None, query, top_k=5, target_section=target_section, paper_sections=paper_sections)
            else:
                context = self.rag.get_context(paper_text, query, top_k=5, target_section=target_section, paper_sections=paper_sections)
        elif isinstance(self.rag, HybridRAG):
            # Hybrid RAG: 需要传入 paper_text（内部会同时使用两种方法）
            context = self.rag.get_context(paper_text, query, top_k=5, target_section=target_section, paper_sections=paper_sections)
        elif isinstance(self.rag, EmbeddingRAG):
            # Embedding RAG: 不需要传入 paper_text（已构建索引）
            context = self.rag.get_context(query, top_k=5, target_section=target_section)
        else:
            # Simple RAG: 需要传入 paper_text
            context = self.rag.get_context(paper_text, query, top_k=5, target_section=target_section, paper_sections=paper_sections)
        
        if not context:
            # 如果没有找到相关上下文，返回不确定的结果
            return {
                'id': claim_id,
                'verification_result': 'Partially_True',
                'verification_reason': 'No relevant context found in the paper to verify this claim.',
                'confidence': 0.3
            }
        
        # 限制上下文长度以避免 token 限制
        max_context_length = 3000
        if len(context) > max_context_length:
            context = context[:max_context_length] + "..."
        
        # 构建验证提示
        prompt = f"""Please verify the following reviewer claim against the paper content.

Reviewer Claim:
Statement: {statement}
Substantiation: {substantiation_content}

Relevant Paper Context:
{context}

Please provide your verification result in the following JSON format:
{{
    "verification_result": "True" | "False" | "Partially_True",
    "verification_reason": "Your detailed explanation here, citing specific evidence from the paper context",
    "confidence": 0.0-1.0
}}"""
        
        try:
            response = self.llm.call(prompt, self.system_prompt, max_tokens=1000)
            
            # 解析 JSON 响应
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            
            # 确保结果格式正确
            verification_result = {
                'id': claim_id,
                'verification_result': result.get('verification_result', 'Partially_True'),
                'verification_reason': result.get('verification_reason', 'Unable to determine'),
                'confidence': float(result.get('confidence', 0.5))
            }
            
            # 验证 verification_result 的值
            if verification_result['verification_result'] not in ['True', 'False', 'Partially_True']:
                verification_result['verification_result'] = 'Partially_True'
            
            return verification_result
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 解析失败 for claim {claim_id}: {e}")
            print(f"[DEBUG] LLM 响应: {response[:500]}")
            return {
                'id': claim_id,
                'verification_result': 'Partially_True',
                'verification_reason': f'Error parsing verification result: {str(e)}',
                'confidence': 0.3
            }
        except Exception as e:
            print(f"[ERROR] 验证观点 {claim_id} 时出错: {e}")
            return {
                'id': claim_id,
                'verification_result': 'Partially_True',
                'verification_reason': f'Error during verification: {str(e)}',
                'confidence': 0.3
            }
    
    def process_claims(self, claims: List[Dict], paper_text: str, paper_sections: Dict[str, str] = None) -> List[Dict]:
        """
        处理多个观点，只验证有证据的观点
        
        Args:
            claims: 观点列表
            paper_text: 论文文本
            paper_sections: 论文的section字典，key为section名，value为section内容
            
        Returns:
            验证结果列表
        """
        verifications = []
        
        # 只处理有证据的观点（substantiation_type != None）
        claims_to_verify = [
            claim for claim in claims 
            if claim.get('substantiation_type') and claim.get('substantiation_type') != 'None'
        ]
        
        print(f"[INFO] 需要验证 {len(claims_to_verify)} 个观点（共 {len(claims)} 个观点）")
        
        for i, claim in enumerate(claims_to_verify, 1):
            print(f"  - Verifying claim {i}/{len(claims_to_verify)}: {claim.get('id', 'unknown')}")
            verification = self.verify_claim(claim, paper_text, paper_sections)
            verifications.append(verification)
            print(f"    Result: {verification['verification_result']} (confidence: {verification['confidence']:.2f})")
        
        return verifications

