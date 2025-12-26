# RAG 实现现状与改进方案

## 当前 RAG 实现分析

### 实现方式

当前 RAG 系统位于 `src/utils/rag.py`，采用**基于关键词匹配的简单检索方法**。

#### 1. 文本分块 (Chunking)

```python
def chunk_text(self, text: str) -> List[str]:
    # 固定大小分块：500 字符
    # 重叠：50 字符
    # 最大块数限制：1000 块（避免内存问题）
```

**特点**：
- 固定大小分块（500 字符）
- 有重叠（50 字符）以保持上下文连续性
- 限制最大块数以避免内存溢出

**问题**：
- 固定大小可能切断完整句子或段落
- 不考虑语义边界（可能在句子中间切分）
- 限制搜索范围（只搜索前 50k 字符）可能遗漏重要信息

#### 2. 关键词提取

```python
def extract_keywords(self, query: str) -> List[str]:
    # 1. 移除停用词（the, a, an, is, are 等）
    # 2. 提取长度 >= 3 的单词
    # 3. 转换为小写
```

**特点**：
- 简单的停用词过滤
- 基于正则表达式提取单词

**问题**：
- 无法识别同义词（如 "novel" 和 "novelty"）
- 无法理解词干（如 "propose" 和 "proposed"）
- 没有考虑词的重要性（TF-IDF 权重）

#### 3. 相关性计算

```python
def calculate_relevance(self, chunk: str, keywords: List[str]) -> float:
    # 计算关键词在文本块中的匹配次数
    # 分数 = 匹配次数 / (关键词总数 * 2)
    # 归一化到 [0, 1]
```

**特点**：
- 基于关键词出现频率
- 简单的计数匹配

**问题**：
- 无法理解语义相似性（如 "method" 和 "approach"）
- 不考虑词序和上下文
- 分数计算过于简单，可能不够准确

#### 4. 检索流程

```python
def retrieve_relevant_chunks(self, paper_text, query, top_k=5):
    # 1. 限制搜索范围：只搜索前 50k 字符
    # 2. 分块
    # 3. 计算每个块的相关性分数
    # 4. 排序并返回 top-k
```

**当前限制**：
- **只搜索前 50k 字符**：可能遗漏论文后半部分的重要信息
- 线性搜索：对每个块都计算分数，效率较低
- 无缓存：每次查询都重新计算

### 当前实现的优缺点

#### 优点
1. **简单快速**：无需额外依赖，实现简单
2. **内存友好**：限制搜索范围，避免内存问题
3. **易于调试**：逻辑清晰，容易理解

#### 缺点
1. **检索精度低**：基于关键词匹配，无法理解语义
2. **覆盖不完整**：只搜索前 50k 字符，可能遗漏重要信息
3. **无法处理同义词**：如 "novel" 和 "novelty" 被视为不同词
4. **相关性计算简单**：不考虑语义相似性
5. **无持久化**：每次运行都重新计算，无法复用

---

## 改进方案

### 方案一：基于 Embedding 的语义检索（推荐）

#### 核心思路
使用预训练的 embedding 模型将文本转换为向量，通过向量相似度进行检索。

#### 实现步骤

**1. 使用 Sentence Transformers**

```python
from sentence_transformers import SentenceTransformer

class EmbeddingRAG:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.chunk_size = 500
        self.chunk_overlap = 50
```

**优势**：
- 理解语义相似性
- 支持多语言
- 模型轻量（all-MiniLM-L6-v2 只有 80MB）

**2. 构建向量数据库**

```python
import faiss
import numpy as np

class EmbeddingRAG:
    def build_index(self, paper_text: str):
        # 1. 分块
        chunks = self.chunk_text(paper_text)
        
        # 2. 生成 embeddings
        embeddings = self.model.encode(chunks)
        
        # 3. 构建 FAISS 索引
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)  # L2 距离
        index.add(embeddings.astype('float32'))
        
        return index, chunks
```

**优势**：
- 快速检索（FAISS 支持 GPU 加速）
- 可持久化（保存索引到磁盘）
- 支持大规模数据

**3. 语义检索**

```python
def retrieve_relevant_chunks(self, query: str, top_k: int = 5):
    # 1. 将查询转换为向量
    query_embedding = self.model.encode([query])
    
    # 2. 在向量空间中搜索最相似的块
    distances, indices = self.index.search(query_embedding, top_k)
    
    # 3. 返回相关块
    return [self.chunks[i] for i in indices[0]]
```

**优势**：
- 理解语义：能找到同义词和相似概念
- 检索速度快：向量相似度计算高效
- 覆盖完整：可以搜索整个论文

#### 完整实现示例

```python
"""
改进的 RAG 实现：基于 Embedding 的语义检索
"""
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import pickle
from pathlib import Path

class EmbeddingRAG:
    def __init__(self, 
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 chunk_size: int = 500,
                 chunk_overlap: int = 50):
        self.model = SentenceTransformer(model_name)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.index = None
        self.chunks = None
        self.dimension = None
    
    def chunk_text(self, text: str) -> List[str]:
        """改进的分块：按段落分割，保持语义完整性"""
        # 先按段落分割
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def build_index(self, paper_text: str, save_path: str = None):
        """构建向量索引"""
        # 分块
        self.chunks = self.chunk_text(paper_text)
        
        # 生成 embeddings
        print(f"Generating embeddings for {len(self.chunks)} chunks...")
        embeddings = self.model.encode(self.chunks, show_progress_bar=True)
        
        # 构建 FAISS 索引
        self.dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings.astype('float32'))
        
        # 保存索引（可选）
        if save_path:
            faiss.write_index(self.index, f"{save_path}.index")
            with open(f"{save_path}.chunks", 'wb') as f:
                pickle.dump(self.chunks, f)
    
    def load_index(self, load_path: str):
        """加载已保存的索引"""
        self.index = faiss.read_index(f"{load_path}.index")
        with open(f"{load_path}.chunks", 'rb') as f:
            self.chunks = pickle.load(f)
        self.dimension = self.index.d
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """语义检索相关块"""
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")
        
        # 查询向量化
        query_embedding = self.model.encode([query])
        
        # 搜索最相似的块
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # 返回结果（距离转换为相似度分数）
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            similarity = 1 / (1 + dist)  # 将距离转换为相似度
            results.append((self.chunks[idx], similarity))
        
        return results
    
    def get_context(self, query: str, top_k: int = 5) -> str:
        """获取合并后的上下文"""
        chunks = self.retrieve_relevant_chunks(query, top_k)
        if not chunks:
            return ""
        
        context_parts = [chunk for chunk, score in chunks]
        return "\n\n".join(context_parts)
```

#### 性能对比

| 指标 | 当前实现 | Embedding RAG |
|------|---------|---------------|
| 检索精度 | 低（关键词匹配） | 高（语义理解） |
| 覆盖范围 | 前 50k 字符 | 完整论文 |
| 检索速度 | 中等（线性搜索） | 快（向量索引） |
| 内存占用 | 低 | 中等（需要存储向量） |
| 可持久化 | 否 | 是 |

---

### 方案二：混合检索（Hybrid Search）

#### 核心思路
结合关键词检索和语义检索，取两者优势。

#### 实现方式

```python
class HybridRAG:
    def __init__(self):
        self.embedding_rag = EmbeddingRAG()
        self.keyword_rag = SimpleRAG()  # 当前实现
    
    def retrieve(self, query: str, top_k: int = 5):
        # 1. 语义检索
        semantic_results = self.embedding_rag.retrieve_relevant_chunks(query, top_k)
        
        # 2. 关键词检索
        keyword_results = self.keyword_rag.retrieve_relevant_chunks(paper_text, query, top_k)
        
        # 3. 合并和重排序
        combined = self._merge_and_rerank(semantic_results, keyword_results)
        
        return combined[:top_k]
```

**优势**：
- 结合精确匹配和语义理解
- 提高召回率（能找到更多相关结果）

---

### 方案三：改进分块策略

#### 核心思路
按论文结构（章节、段落）进行智能分块，而非固定大小。

#### 实现方式

```python
def smart_chunk_text(self, paper_text: str) -> List[Dict]:
    """按论文结构分块"""
    chunks = []
    
    # 识别章节标题
    sections = self.extract_sections(paper_text)
    
    for section_name, section_content in sections.items():
        # 按段落分割
        paragraphs = section_content.split('\n\n')
        
        # 合并小段落，保持语义完整性
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) < 500:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'section': section_name,
                        'metadata': {'type': 'paragraph'}
                    })
                current_chunk = para + "\n\n"
    
    return chunks
```

**优势**：
- 保持语义完整性
- 保留章节信息（可用于过滤）
- 更符合论文结构

---

### 方案四：查询扩展（Query Expansion）

#### 核心思路
扩展查询词，包括同义词和相关概念。

#### 实现方式

```python
def expand_query(self, query: str) -> str:
    """扩展查询"""
    # 1. 提取关键词
    keywords = self.extract_keywords(query)
    
    # 2. 使用同义词库或 LLM 生成同义词
    expanded_keywords = []
    for keyword in keywords:
        synonyms = self.get_synonyms(keyword)  # 使用 WordNet 或 LLM
        expanded_keywords.extend(synonyms)
    
    # 3. 组合原始查询和扩展词
    expanded_query = query + " " + " ".join(expanded_keywords)
    
    return expanded_query
```

**优势**：
- 提高召回率
- 能找到使用不同词汇表达的相关内容

---

### 方案五：重排序（Reranking）

#### 核心思路
使用更强大的模型对初步检索结果进行重排序。

#### 实现方式

```python
from sentence_transformers import CrossEncoder

class RerankingRAG:
    def __init__(self):
        self.retriever = EmbeddingRAG()  # 初步检索
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')  # 重排序模型
    
    def retrieve(self, query: str, top_k: int = 5):
        # 1. 初步检索（返回更多结果）
        candidates = self.retriever.retrieve_relevant_chunks(query, top_k=20)
        
        # 2. 重排序
        pairs = [[query, chunk] for chunk, _ in candidates]
        scores = self.reranker.predict(pairs)
        
        # 3. 按新分数排序
        reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        
        return [chunk for (chunk, _), _ in reranked[:top_k]]
```

**优势**：
- 提高检索精度
- 考虑查询和文档的交互

---

## 推荐实施路线

### 阶段一：基础改进（立即实施）

1. **实施 Embedding RAG**
   - 使用 `sentence-transformers/all-MiniLM-L6-v2`
   - 集成 FAISS 进行快速检索
   - 支持索引持久化

2. **改进分块策略**
   - 按段落而非固定大小分块
   - 保持语义完整性

3. **移除搜索范围限制**
   - 搜索完整论文内容

### 阶段二：性能优化（中期）

1. **实施混合检索**
   - 结合关键词和语义检索
   - 提高召回率

2. **查询扩展**
   - 使用同义词库或 LLM 扩展查询

### 阶段三：高级功能（长期）

1. **重排序**
   - 使用 Cross-Encoder 进行精确排序

2. **多模态支持**
   - 处理论文中的图表和公式

3. **缓存机制**
   - 缓存常见查询的结果

---

## 实施建议

### 优先级排序

1. **高优先级**：Embedding RAG + 改进分块
   - 最大程度提升检索精度
   - 实施难度中等

2. **中优先级**：移除搜索限制 + 索引持久化
   - 提高覆盖范围
   - 提升运行效率

3. **低优先级**：混合检索 + 重排序
   - 进一步优化精度
   - 需要更多计算资源

### 依赖项

```txt
sentence-transformers>=2.2.0
faiss-cpu>=1.7.4  # 或 faiss-gpu（如果有 GPU）
numpy>=1.21.0
```

### 配置更新

```yaml
rag:
  method: "embedding"  # "simple" 或 "embedding"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  chunk_size: 500
  chunk_overlap: 50
  top_k: 5
  use_cache: true
  index_path: "data/processed/rag_indices"
```

---

## 预期效果

### 检索精度提升

- **当前**：基于关键词匹配，可能遗漏语义相关但用词不同的内容
- **改进后**：理解语义，能找到同义词和相关概念

### 覆盖范围提升

- **当前**：只搜索前 50k 字符
- **改进后**：搜索完整论文

### 性能提升

- **当前**：每次查询都重新计算
- **改进后**：索引可持久化，查询速度更快

### 实际案例

假设查询："The method uses attention mechanism"

**当前实现**：
- 只能找到包含 "attention mechanism" 的文本
- 可能遗漏使用 "self-attention" 或 "transformer" 的相关段落

**改进后**：
- 能找到所有语义相关的段落
- 包括使用不同词汇表达相同概念的内容

---

## 总结

当前 RAG 实现虽然简单快速，但在检索精度和覆盖范围上存在明显不足。通过引入 Embedding 模型和向量数据库，可以显著提升系统的检索能力，更好地支持论文验证任务。

建议优先实施 Embedding RAG，这是性价比最高的改进方案。

