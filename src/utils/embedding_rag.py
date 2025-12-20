"""
基于 Embedding 的 RAG 实现
使用 Sentence Transformers 和 FAISS 进行语义检索
"""

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Optional, Dict
import pickle
from pathlib import Path
import os


class EmbeddingRAG:
    """基于 Embedding 的语义检索 RAG"""
    
    def __init__(self, 
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 chunk_size: int = 500,
                 chunk_overlap: int = 50):
        """
        Args:
            model_name: Sentence Transformer 模型名称
            chunk_size: 文本块大小（字符数）
            chunk_overlap: 文本块重叠大小
        """
        print(f"[RAG] Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.index = None
        self.chunks = None
        self.chunk_sections = None  # 存储每个chunk所属的section
        self.dimension = None
        self._is_built = False
    
    def chunk_text(self, text: str) -> List[str]:
        """
        将文本分割成块（改进版：优先按段落分割）
        
        Args:
            text: 原始文本
            
        Returns:
            文本块列表
        """
        chunks = []
        
        # 先按段落分割（双换行）
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果当前块加上新段落不超过限制，则合并
            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果单个段落就超过限制，强制分割
                if len(para) > self.chunk_size:
                    # 按句子分割
                    sentences = para.split('. ')
                    temp_chunk = ""
                    for sent in sentences:
                        if len(temp_chunk) + len(sent) + 2 <= self.chunk_size:
                            if temp_chunk:
                                temp_chunk += ". " + sent
                            else:
                                temp_chunk = sent
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk)
                            temp_chunk = sent
                    if temp_chunk:
                        current_chunk = temp_chunk
                else:
                    current_chunk = para
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        # 如果块太多，进行重叠处理
        if len(chunks) > 1000:
            print(f"[RAG] Warning: Too many chunks ({len(chunks)}), limiting to 1000")
            chunks = chunks[:1000]
        
        return chunks
    
    def build_index(self, paper_text: str, save_path: Optional[str] = None, paper_sections: Dict[str, str] = None):
        """
        构建向量索引
        
        Args:
            paper_text: 论文文本
            save_path: 保存索引的路径（可选，不含扩展名）
            paper_sections: 论文的section字典，用于标记chunk所属的section
        """
        print(f"[RAG] Building index from paper text...")
        
        # 分块
        self.chunks = self.chunk_text(paper_text)
        print(f"[RAG] Created {len(self.chunks)} chunks")
        
        if not self.chunks:
            raise ValueError("No chunks created from paper text")
        
        # 如果提供了paper_sections，标记每个chunk所属的section
        self.chunk_sections = [None] * len(self.chunks)
        if paper_sections:
            # 构建section到文本位置的映射（按顺序）
            section_positions = []
            current_pos = 0
            for section_name, section_content in paper_sections.items():
                # 尝试找到section在原文中的位置
                section_start = paper_text.find(section_content, current_pos)
                if section_start != -1:
                    section_positions.append((section_name, section_start, section_start + len(section_content)))
                    current_pos = section_start + len(section_content)
            
            # 标记每个chunk所属的section
            # 使用累积位置来跟踪chunk在原文中的位置
            chunk_positions = []
            cumulative_pos = 0
            for chunk in self.chunks:
                # 尝试在原文中找到chunk的位置
                chunk_start = paper_text.find(chunk, cumulative_pos)
                if chunk_start != -1:
                    chunk_positions.append((chunk_start, chunk_start + len(chunk)))
                    cumulative_pos = chunk_start + len(chunk)
                else:
                    # 如果找不到，使用累积位置（可能chunk被修改了）
                    chunk_positions.append((cumulative_pos, cumulative_pos + len(chunk)))
                    cumulative_pos += len(chunk)
            
            # 为每个chunk分配section（按顺序匹配，找到第一个包含该chunk的section）
            for i, (chunk_start, chunk_end) in enumerate(chunk_positions):
                chunk_center = (chunk_start + chunk_end) / 2
                for section_name, sec_start, sec_end in section_positions:
                    # 如果chunk的中心点在section范围内，则属于该section
                    if sec_start <= chunk_center <= sec_end:
                        self.chunk_sections[i] = section_name
                        break
                # 如果中心点不在任何section内，检查是否有重叠
                if self.chunk_sections[i] is None:
                    for section_name, sec_start, sec_end in section_positions:
                        if chunk_start < sec_end and chunk_end > sec_start:
                            self.chunk_sections[i] = section_name
                            break
        
        # 生成 embeddings
        print(f"[RAG] Generating embeddings...")
        embeddings = self.model.encode(
            self.chunks, 
            show_progress_bar=True,
            batch_size=32,
            convert_to_numpy=True
        )
        
        print(f"[RAG] Embeddings shape: {embeddings.shape}")
        
        # 构建 FAISS 索引
        self.dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # 归一化向量（使用 L2 归一化，这样 L2 距离等价于余弦距离）
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
        
        self._is_built = True
        print(f"[RAG] Index built successfully with {self.index.ntotal} vectors")
        
        # 保存索引（可选）
        if save_path:
            self.save_index(save_path)
    
    def save_index(self, save_path: str):
        """
        保存索引到磁盘
        
        Args:
            save_path: 保存路径（不含扩展名）
        """
        if not self._is_built:
            raise ValueError("Index not built. Call build_index() first.")
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存 FAISS 索引
        faiss.write_index(self.index, str(save_path) + ".index")
        
        # 保存文本块
        with open(str(save_path) + ".chunks", 'wb') as f:
            pickle.dump(self.chunks, f)
        
        # 保存chunk_sections（如果存在）
        if self.chunk_sections:
            with open(str(save_path) + ".sections", 'wb') as f:
                pickle.dump(self.chunk_sections, f)
        
        # 保存元数据
        metadata = {
            'dimension': self.dimension,
            'num_chunks': len(self.chunks),
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'has_sections': self.chunk_sections is not None
        }
        with open(str(save_path) + ".meta", 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"[RAG] Index saved to {save_path}")
    
    def load_index(self, load_path: str):
        """
        从磁盘加载索引
        
        Args:
            load_path: 加载路径（不含扩展名）
        """
        load_path = Path(load_path)
        
        # 加载 FAISS 索引
        if not (load_path.with_suffix('.index')).exists():
            raise FileNotFoundError(f"Index file not found: {load_path}.index")
        
        self.index = faiss.read_index(str(load_path) + ".index")
        
        # 加载文本块
        with open(str(load_path) + ".chunks", 'rb') as f:
            self.chunks = pickle.load(f)
        
        # 加载chunk_sections（如果存在）
        sections_path = load_path.with_suffix('.sections')
        if sections_path.exists():
            with open(str(sections_path), 'rb') as f:
                self.chunk_sections = pickle.load(f)
        else:
            self.chunk_sections = None
        
        # 加载元数据
        if (load_path.with_suffix('.meta')).exists():
            with open(str(load_path) + ".meta", 'rb') as f:
                metadata = pickle.load(f)
                self.dimension = metadata.get('dimension', self.index.d)
        else:
            self.dimension = self.index.d
        
        self._is_built = True
        print(f"[RAG] Index loaded: {self.index.ntotal} vectors, {len(self.chunks)} chunks")
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 5, target_section: str = None) -> List[Tuple[str, float]]:
        """
        语义检索相关文本块
        
        Args:
            query: 查询文本
            top_k: 返回前 k 个最相关的块
            target_section: 目标section名称（如果指定，只在该section中检索）
            
        Returns:
            (文本块, 相似度分数) 的列表，按分数降序排列
        """
        if not self._is_built or self.index is None:
            raise ValueError("Index not built. Call build_index() or load_index() first.")
        
        # 查询向量化
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # 归一化查询向量
        faiss.normalize_L2(query_embedding)
        
        # 如果指定了target_section，需要先找到匹配的chunk索引
        valid_indices = None
        if target_section and self.chunk_sections:
            # 找到属于target_section的chunk索引
            valid_indices = set()
            for i, chunk_section in enumerate(self.chunk_sections):
                if chunk_section:
                    # 模糊匹配section名称
                    if target_section.lower() in chunk_section.lower() or chunk_section.lower() in target_section.lower():
                        valid_indices.add(i)
            
            if not valid_indices:
                print(f"[WARNING] No chunks found in section '{target_section}', using all chunks")
                valid_indices = None
        
        # 搜索最相似的块（如果指定了section，需要搜索更多以过滤）
        search_k = top_k * 3 if valid_indices else top_k
        distances, indices = self.index.search(query_embedding.astype('float32'), search_k)
        
        # 将距离转换为相似度分数（L2 归一化后，距离越小相似度越高）
        # 使用 1 - distance 作为相似度（因为距离在 [0, 2] 范围内）
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.chunks):
                # 如果指定了section，只返回属于该section的chunk
                if valid_indices is not None and idx not in valid_indices:
                    continue
                
                similarity = 1.0 - (dist / 2.0)  # 归一化到 [0, 1]
                similarity = max(0.0, min(1.0, similarity))  # 确保在 [0, 1] 范围内
                results.append((self.chunks[idx], similarity))
                
                # 如果已经找到足够的chunk，停止
                if len(results) >= top_k:
                    break
        
        return results
    
    def get_context(self, query: str, top_k: int = 5, target_section: str = None) -> str:
        """
        获取与查询相关的上下文（合并多个块）
        
        Args:
            query: 查询文本
            top_k: 返回前 k 个最相关的块
            target_section: 目标section名称（如果指定，只在该section中检索）
            
        Returns:
            合并后的上下文文本
        """
        chunks = self.retrieve_relevant_chunks(query, top_k, target_section)
        if not chunks:
            return ""
        
        # 合并前 k 个块
        context_parts = [chunk for chunk, score in chunks]
        return "\n\n".join(context_parts)
    
    def is_built(self) -> bool:
        """检查索引是否已构建"""
        return self._is_built

