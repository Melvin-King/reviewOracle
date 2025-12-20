# 重排序（Reranking）功能实现说明

## 概述

重排序功能使用 Cross-Encoder 对初步检索结果进行重新排序，提高检索精度。这是 RAG 系统优化的重要功能之一。

## 实现原理

### 工作流程

1. **初步检索**：使用基础 RAG（SimpleRAG、EmbeddingRAG 或 HybridRAG）进行初步检索，返回更多候选（默认 20 个）
2. **重排序**：使用 Cross-Encoder 对候选结果进行重新评分
3. **返回结果**：按重排序分数排序，返回 top_k 个最相关的结果

### 为什么需要重排序？

- **初步检索的局限性**：基于关键词或 Embedding 的检索可能不够精确
- **Cross-Encoder 的优势**：能够同时考虑查询和文档的交互，提供更准确的相似度评分
- **精度提升**：预期检索精度提升 10-20%

## 使用方法

### 1. 配置文件设置

在 `config.yaml` 中启用重排序：

```yaml
rag:
  method: "hybrid"  # 或 "simple", "embedding"
  use_reranking: true  # 启用重排序
  reranker_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"  # Cross-Encoder 模型
  reranking_initial_top_k: 20  # 初步检索返回的候选数量
```

### 2. 代码使用

```python
from src.utils.reranking_rag import RerankingRAG
from src.utils.hybrid_rag import HybridRAG

# 创建基础 RAG
base_rag = HybridRAG(...)

# 创建带重排序的 RAG
reranking_rag = RerankingRAG(
    base_rag=base_rag,
    reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
    initial_top_k=20,
    use_reranking=True
)

# 使用（接口与基础 RAG 相同）
context = reranking_rag.get_context(paper_text, query, top_k=5)
```

## 架构设计

### RerankingRAG 类

`RerankingRAG` 是一个包装类，可以包装任何基础 RAG 实现：

- **SimpleRAG**：基于关键词匹配
- **EmbeddingRAG**：基于语义检索
- **HybridRAG**：混合检索

### 接口兼容性

`RerankingRAG` 实现了与基础 RAG 相同的接口，可以无缝替换：

- `retrieve_relevant_chunks()`: 检索相关文本块
- `get_context()`: 获取合并后的上下文
- `build_index()`: 构建索引（委托给基础 RAG）
- `load_index()`: 加载索引（委托给基础 RAG）
- `is_built()`: 检查索引是否已构建

### Section 过滤支持

重排序功能完全支持 section 过滤：

```python
context = reranking_rag.get_context(
    paper_text, query, top_k=5,
    target_section="Experiments",
    paper_sections=paper_sections
)
```

## 性能考虑

### 计算开销

- **初步检索**：与基础 RAG 相同
- **重排序**：Cross-Encoder 需要对每个候选进行推理，计算开销较高
- **优化建议**：
  - 控制 `initial_top_k` 不要太大（建议 10-30）
  - 使用较小的 Cross-Encoder 模型（如 `ms-marco-MiniLM-L-6-v2`）

### 缓存策略

- Cross-Encoder 模型会在首次使用时加载
- 建议在生产环境中预热模型

## 测试结果

测试显示重排序功能正常工作：

1. ✅ 重排序改变了结果顺序
2. ✅ 与基础 RAG 接口兼容
3. ✅ 支持禁用重排序（`use_reranking=False`）
4. ✅ 支持所有基础 RAG 类型

## 配置选项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `use_reranking` | bool | `false` | 是否启用重排序 |
| `reranker_model` | str | `"cross-encoder/ms-marco-MiniLM-L-6-v2"` | Cross-Encoder 模型名称 |
| `reranking_initial_top_k` | int | `20` | 初步检索返回的候选数量 |

## 模型选择

推荐的 Cross-Encoder 模型：

- **ms-marco-MiniLM-L-6-v2**（推荐）：速度快，精度好
- **ms-marco-MiniLM-L-12-v2**：精度更高，但速度较慢
- **cross-encoder/ms-marco-electra-base**：精度最高，但速度最慢

## 注意事项

1. **首次使用**：Cross-Encoder 模型会在首次使用时自动下载
2. **内存占用**：Cross-Encoder 模型会占用一定内存
3. **计算时间**：重排序会增加检索时间，但通常可以接受（< 1秒）
4. **兼容性**：完全兼容现有的 section 过滤功能

## 未来改进

- [ ] 支持批量重排序（提高效率）
- [ ] 支持自定义重排序模型
- [ ] 添加重排序结果的缓存机制
- [ ] 支持重排序分数的可视化

