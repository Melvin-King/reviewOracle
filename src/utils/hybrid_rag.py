"""
混合 RAG 实现
结合关键词匹配（SimpleRAG）和语义检索（EmbeddingRAG）的优势
"""

from typing import List, Tuple, Optional, Dict
from collections import defaultdict
from .rag import SimpleRAG
from .embedding_rag import EmbeddingRAG


class HybridRAG:
    """混合 RAG：结合关键词匹配和语义检索"""
    
    def __init__(self,
                 keyword_weight: float = 0.3,
                 semantic_weight: float = 0.7,
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 chunk_size: int = 500,
                 chunk_overlap: int = 50):
        """
        Args:
            keyword_weight: 关键词匹配结果的权重（0-1）
            semantic_weight: 语义检索结果的权重（0-1）
            embedding_model: Embedding 模型名称
            chunk_size: 文本块大小
            chunk_overlap: 文本块重叠大小
        """
        # 确保权重和为 1.0
        total_weight = keyword_weight + semantic_weight
        if total_weight > 0:
            self.keyword_weight = keyword_weight / total_weight
            self.semantic_weight = semantic_weight / total_weight
        else:
            self.keyword_weight = 0.5
            self.semantic_weight = 0.5
        
        # 初始化两种 RAG
        self.keyword_rag = SimpleRAG(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.semantic_rag = EmbeddingRAG(
            model_name=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def build_index(self, paper_text: str, save_path: Optional[str] = None, paper_sections: Dict[str, str] = None):
        """
        构建语义检索索引（关键词 RAG 不需要预构建）
        
        Args:
            paper_text: 论文文本
            save_path: 索引保存路径
            paper_sections: 论文的section字典，用于标记chunk所属的section
        """
        self.semantic_rag.build_index(paper_text, save_path, paper_sections)
    
    def load_index(self, load_path: str):
        """加载语义检索索引"""
        self.semantic_rag.load_index(load_path)
    
    def is_built(self) -> bool:
        """检查语义索引是否已构建"""
        return self.semantic_rag.is_built()
    
    def retrieve_relevant_chunks(self, paper_text: str, query: str, top_k: int = 5,
                                  target_section: str = None, paper_sections: Dict[str, str] = None) -> List[Tuple[str, float]]:
        """
        混合检索相关文本块
        
        Args:
            paper_text: 论文文本（用于关键词检索）
            query: 查询文本
            top_k: 返回前 k 个最相关的块
            target_section: 目标section名称（如果指定，只在该section中检索）
            paper_sections: 论文的section字典，key为section名，value为section内容
            
        Returns:
            (文本块, 加权分数) 的列表，按分数降序排列
        """
        # 1. 关键词检索
        keyword_results = self.keyword_rag.retrieve_relevant_chunks(
            paper_text, query, top_k=top_k * 2, 
            target_section=target_section, paper_sections=paper_sections
        )
        
        # 2. 语义检索（如果索引已构建）
        semantic_results = []
        if self.semantic_rag.is_built():
            try:
                semantic_results = self.semantic_rag.retrieve_relevant_chunks(
                    query, top_k=top_k * 2, target_section=target_section
                )
            except Exception as e:
                print(f"[WARNING] Semantic retrieval failed: {e}, using keyword only")
        
        # 3. 合并和加权
        chunk_scores = defaultdict(lambda: {'keyword': 0.0, 'semantic': 0.0, 'count': 0})
        
        # 记录关键词检索结果
        for chunk, score in keyword_results:
            chunk_scores[chunk]['keyword'] = max(chunk_scores[chunk]['keyword'], score)
            chunk_scores[chunk]['count'] += 1
        
        # 记录语义检索结果
        for chunk, score in semantic_results:
            chunk_scores[chunk]['semantic'] = max(chunk_scores[chunk]['semantic'], score)
            chunk_scores[chunk]['count'] += 1
        
        # 4. 计算加权分数
        final_results = []
        for chunk, scores in chunk_scores.items():
            # 加权平均
            weighted_score = (
                scores['keyword'] * self.keyword_weight +
                scores['semantic'] * self.semantic_weight
            )
            
            # 如果两种方法都找到了，给予奖励
            if scores['count'] > 1:
                weighted_score *= 1.1  # 10% 奖励
            
            final_results.append((chunk, weighted_score))
        
        # 5. 按分数排序并返回 top-k
        final_results.sort(key=lambda x: x[1], reverse=True)
        return final_results[:top_k]
    
    def get_context(self, paper_text: str, query: str, top_k: int = 5,
                    target_section: str = None, paper_sections: Dict[str, str] = None) -> str:
        """
        获取与查询相关的上下文（合并多个块）
        
        Args:
            paper_text: 论文文本
            query: 查询文本
            top_k: 返回前 k 个最相关的块
            target_section: 目标section名称（如果指定，只在该section中检索）
            paper_sections: 论文的section字典，key为section名，value为section内容
            
        Returns:
            合并后的上下文文本
        """
        chunks = self.retrieve_relevant_chunks(paper_text, query, top_k, target_section, paper_sections)
        if not chunks:
            return ""
        
        # 合并前 k 个块
        context_parts = [chunk for chunk, score in chunks]
        return "\n\n".join(context_parts)

