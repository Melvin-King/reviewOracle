# Embedding RAG 使用说明

## 概述

已实现基于 Embedding 的语义检索 RAG 系统，使用 Sentence Transformers 和 FAISS 进行高效的向量检索。

## 主要特性

1. **语义理解**：使用预训练模型理解文本语义，而非简单的关键词匹配
2. **完整覆盖**：可以搜索整个论文，不再限制在前 50k 字符
3. **快速检索**：使用 FAISS 向量索引，检索速度快
4. **索引持久化**：可以保存和加载索引，避免重复计算
5. **向后兼容**：可以切换回 Simple RAG（关键词匹配）

## 文件结构

```
src/utils/
├── rag.py              # SimpleRAG（关键词匹配）
└── embedding_rag.py    # EmbeddingRAG（语义检索）
```

## 配置

在 `config.yaml` 中配置：

```yaml
rag:
  method: "embedding"  # "simple" 或 "embedding"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  top_k: 5
  chunk_size: 500
  chunk_overlap: 50
  use_cache: true  # 是否缓存索引
  index_path: "data/processed/rag_indices"  # 索引保存路径
```

### 配置说明

- `method`: 选择 RAG 方法
  - `"simple"`: 使用关键词匹配（原有方法）
  - `"embedding"`: 使用语义检索（新方法）
  
- `embedding_model`: Sentence Transformer 模型名称
  - 推荐：`"sentence-transformers/all-MiniLM-L6-v2"`（轻量，80MB）
  - 其他选项：`"sentence-transformers/all-mpnet-base-v2"`（更准确，420MB）

- `use_cache`: 是否缓存索引到磁盘
  - `true`: 首次构建后保存，后续直接加载（推荐）
  - `false`: 每次都在内存中构建（不保存）

- `index_path`: 索引保存路径
  - 每个论文的索引会保存为：`{index_path}/{paper_id}.index`

## 使用方法

### 自动使用（推荐）

在 Pipeline 中自动使用，无需额外配置：

```python
from src.pipeline import EVWPipeline

pipeline = EVWPipeline()  # 会根据 config.yaml 自动选择 RAG 方法
result = pipeline.step2_verification("paper_19076")
```

### 手动使用

```python
from src.utils.embedding_rag import EmbeddingRAG
from src.data.data_loader import DataLoader

# 初始化
rag = EmbeddingRAG(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    chunk_size=500,
    chunk_overlap=50
)

# 加载论文文本
data_loader = DataLoader()
paper_text = data_loader.load_paper_text("paper_19076")

# 构建索引（首次）
rag.build_index(paper_text, save_path="data/processed/rag_indices/paper_19076")

# 检索
query = "The method uses attention mechanism"
context = rag.get_context(query, top_k=5)
print(context)

# 或者加载已保存的索引
rag.load_index("data/processed/rag_indices/paper_19076")
context = rag.get_context(query, top_k=5)
```

## 工作流程

### 首次运行（构建索引）

1. 加载论文文本
2. 将文本分块（按段落优先，保持语义完整性）
3. 使用 Sentence Transformer 生成每个块的 embedding
4. 构建 FAISS 向量索引
5. （可选）保存索引到磁盘

### 后续运行（使用缓存）

1. 检查是否存在已保存的索引
2. 如果存在，直接加载索引
3. 如果不存在，重新构建

### 检索过程

1. 将查询文本转换为 embedding
2. 在向量空间中搜索最相似的文本块
3. 返回 top-k 最相关的块

## 性能对比

| 指标 | Simple RAG | Embedding RAG |
|------|-----------|---------------|
| 检索精度 | 低（关键词匹配） | 高（语义理解） |
| 覆盖范围 | 前 50k 字符 | 完整论文 |
| 首次构建时间 | 快（< 1秒） | 中等（10-30秒） |
| 检索速度 | 中等 | 快（向量索引） |
| 内存占用 | 低 | 中等（需要存储向量） |
| 可持久化 | 否 | 是 |

## 测试

运行测试脚本验证实现：

```bash
python test_embedding_rag.py
```

测试包括：
1. RAG 初始化
2. 论文文本加载
3. 索引构建
4. 检索功能
5. 索引保存和加载

## 切换回 Simple RAG

如果需要切换回关键词匹配方法，只需修改 `config.yaml`：

```yaml
rag:
  method: "simple"  # 改为 "simple"
```

## 常见问题

### Q: 首次运行很慢？

A: 首次运行需要下载模型和构建索引，这是正常的。后续运行会使用缓存的索引，速度会快很多。

### Q: 索引文件很大？

A: 每个论文的索引大约占用几 MB 到几十 MB（取决于论文长度）。这是正常的，因为需要存储向量。

### Q: 如何清理索引缓存？

A: 删除 `data/processed/rag_indices/` 目录下的文件即可。下次运行会重新构建。

### Q: 可以使用 GPU 加速吗？

A: 可以。安装 `faiss-gpu` 替代 `faiss-cpu`，FAISS 会自动使用 GPU 加速。

```bash
pip uninstall faiss-cpu
pip install faiss-gpu
```

## 改进建议

1. **使用更大的模型**：如果需要更高的精度，可以使用 `all-mpnet-base-v2`
2. **调整分块大小**：根据论文特点调整 `chunk_size` 和 `chunk_overlap`
3. **添加重排序**：使用 Cross-Encoder 对初步检索结果进行重排序
4. **批量处理**：对多个论文批量构建索引

## 技术细节

### Embedding 模型

- **all-MiniLM-L6-v2**: 轻量级模型，速度快，适合大多数场景
- **all-mpnet-base-v2**: 更准确的模型，但更大更慢

### FAISS 索引

- **IndexFlatL2**: 精确搜索，使用 L2 距离
- 向量归一化：使用 L2 归一化，使 L2 距离等价于余弦距离

### 相似度计算

- 距离转换为相似度：`similarity = 1.0 - (distance / 2.0)`
- 归一化到 [0, 1] 范围

## 总结

基于 Embedding 的 RAG 显著提升了检索精度和覆盖范围，是推荐使用的方案。通过索引缓存机制，可以平衡首次构建时间和后续检索速度。

