"""
RAG (Retrieval-Augmented Generation) 工具
用于从论文文本中检索相关段落

提供两种实现：
1. SimpleRAG: 基于关键词匹配的简单实现
2. EmbeddingRAG: 基于 Embedding 的语义检索（见 embedding_rag.py）
"""

from typing import List, Dict, Tuple, Optional
import re
from collections import Counter


class SimpleRAG:
    """简单的 RAG 实现（基于关键词匹配和文本相似度）"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Args:
            chunk_size: 文本块大小（字符数）
            chunk_overlap: 文本块重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """
        将文本分割成块
        
        Args:
            text: 原始文本
            
        Returns:
            文本块列表
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        # 限制最大块数以避免内存问题
        max_chunks = 1000
        
        while start < text_length and len(chunks) < max_chunks:
            end = min(start + self.chunk_size, text_length)
            chunk = text[start:end]
            if chunk.strip():  # 只添加非空块
                chunks.append(chunk)
            start = end - self.chunk_overlap
            if start >= text_length:
                break
        
        return chunks
    
    def extract_keywords(self, query: str) -> List[str]:
        """
        从查询中提取关键词
        
        Args:
            query: 查询文本
            
        Returns:
            关键词列表
        """
        # 移除常见停用词和标点
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        # 提取单词（转换为小写）
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        keywords = [w for w in words if w not in stop_words]
        
        return keywords
    
    def calculate_relevance(self, chunk: str, keywords: List[str]) -> float:
        """
        计算文本块与关键词的相关性分数
        
        Args:
            chunk: 文本块
            query: 关键词列表
            
        Returns:
            相关性分数（0-1）
        """
        chunk_lower = chunk.lower()
        keyword_counts = Counter(keywords)
        
        # 计算关键词匹配度
        matches = 0
        total_keywords = len(keywords)
        
        if total_keywords == 0:
            return 0.0
        
        for keyword in keywords:
            if keyword in chunk_lower:
                matches += keyword_counts[keyword]
        
        # 基础分数：匹配的关键词比例
        base_score = matches / (total_keywords * 2)  # 允许重复匹配
        
        # 归一化到 0-1
        return min(base_score, 1.0)
    
    def retrieve_relevant_chunks(self, paper_text: str, query: str, top_k: int = 5, 
                                  target_section: str = None, paper_sections: Dict[str, str] = None) -> List[Tuple[str, float]]:
        """
        检索与查询相关的文本块
        
        Args:
            paper_text: 论文文本
            query: 查询文本（claim statement + substantiation）
            top_k: 返回前 k 个最相关的块
            target_section: 目标section名称（如果指定，只在该section中检索）
            paper_sections: 论文的section字典，key为section名，value为section内容
            
        Returns:
            (文本块, 相关性分数) 的列表，按分数降序排列
        """
        # 如果指定了target_section，只在该section中检索
        if target_section and paper_sections:
            # 尝试找到匹配的section
            matched_section = None
            for section_name, section_content in paper_sections.items():
                if target_section.lower() in section_name.lower() or section_name.lower() in target_section.lower():
                    matched_section = section_content
                    break
            
            if matched_section:
                search_text = matched_section
            else:
                # 如果找不到匹配的section，使用全文
                print(f"[WARNING] Section '{target_section}' not found, using full text")
                search_text = paper_text
        else:
            search_text = paper_text
        
        # 提取关键词
        keywords = self.extract_keywords(query)
        
        if not keywords:
            return []
        
        # 如果文本太长，先进行粗略搜索找到最相关的区域
        # 限制搜索范围以避免内存问题
        max_search_length = 50000  # 限制搜索前50k字符
        if len(search_text) > max_search_length:
            search_text = search_text[:max_search_length]
        
        # 分割文本
        chunks = self.chunk_text(search_text)
        
        # 计算每个块的相关性
        chunk_scores = []
        for chunk in chunks:
            score = self.calculate_relevance(chunk, keywords)
            if score > 0:
                chunk_scores.append((chunk, score))
        
        # 按分数排序并返回前 k 个
        chunk_scores.sort(key=lambda x: x[1], reverse=True)
        return chunk_scores[:top_k]
    
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


