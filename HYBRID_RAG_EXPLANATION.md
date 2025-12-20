# 混合 RAG 实现说明

## 概述

混合 RAG（HybridRAG）结合了关键词匹配（SimpleRAG）和语义检索（EmbeddingRAG）的优势，通过加权融合两种方法的检索结果，提供更准确和全面的检索效果。

## 设计理念

### 为什么需要混合？

1. **关键词匹配的优势**：
   - 精确匹配：能找到包含确切关键词的文本
   - 快速：无需构建索引
   - 适合：技术术语、专有名词

2. **语义检索的优势**：
   - 理解语义：能找到同义词和相关概念
   - 完整覆盖：搜索整个论文
   - 适合：概念性查询、抽象描述

3. **混合的优势**：
   - 结合两者：既保证精确性，又保证语义理解
   - 加权融合：可配置权重比例
   - 奖励机制：两种方法都找到的文本块获得额外奖励

## 实现原理

### 1. 双重检索

```python
# 同时进行两种检索
keyword_results = keyword_rag.retrieve_relevant_chunks(paper_text, query, top_k=10)
semantic_results = semantic_rag.retrieve_relevant_chunks(query, top_k=10)
```

### 2. 结果合并

```python
# 使用字典记录每个文本块的分数
chunk_scores = {
    "chunk_text": {
        'keyword': 0.8,    # 关键词匹配分数
        'semantic': 0.6,   # 语义检索分数
        'count': 2         # 被找到的次数
    }
}
```

### 3. 加权计算

```python
# 加权平均
weighted_score = (
    keyword_score * keyword_weight +  # 默认 0.3
    semantic_score * semantic_weight  # 默认 0.7
)

# 如果两种方法都找到，给予 10% 奖励
if count > 1:
    weighted_score *= 1.1
```

### 4. 排序返回

```python
# 按加权分数排序，返回 top-k
final_results.sort(key=lambda x: x[1], reverse=True)
return final_results[:top_k]
```

## 配置方式

在 `config.yaml` 中配置：

```yaml
rag:
  method: "hybrid"  # 使用混合 RAG
  keyword_weight: 0.3   # 关键词匹配权重（30%）
  semantic_weight: 0.7  # 语义检索权重（70%）
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  use_cache: true
  index_path: "data/processed/rag_indices"
```

### 权重配置建议

1. **默认配置（推荐）**：
   - `keyword_weight: 0.3`
   - `semantic_weight: 0.7`
   - 适合大多数场景，偏重语义理解

2. **精确匹配优先**：
   - `keyword_weight: 0.6`
   - `semantic_weight: 0.4`
   - 适合技术术语较多的查询

3. **语义理解优先**：
   - `keyword_weight: 0.2`
   - `semantic_weight: 0.8`
   - 适合概念性、抽象性查询

## 工作流程

```
查询输入
    │
    ├─► 关键词检索 (SimpleRAG)
    │   └─► 提取关键词 → 匹配文本块 → 计算相关性分数
    │
    ├─► 语义检索 (EmbeddingRAG)
    │   └─► 向量化查询 → 向量相似度搜索 → 计算相似度分数
    │
    └─► 结果融合
        ├─► 合并结果（去重）
        ├─► 加权计算
        ├─► 奖励机制（两种方法都找到的块）
        └─► 排序返回 top-k
```

## 优势分析

### 1. 提高召回率（Recall）

- 关键词检索可能遗漏语义相关但用词不同的内容
- 语义检索可能遗漏精确匹配的内容
- 混合检索能同时覆盖两种情况

### 2. 提高精确率（Precision）

- 两种方法都找到的文本块更可能是真正相关的
- 奖励机制进一步提升了这些块的排名

### 3. 灵活性

- 可根据场景调整权重
- 可以禁用其中一种方法（权重设为 0）

## 使用示例

### 示例 1：技术术语查询

**查询**："attention mechanism"

**关键词检索**：找到包含 "attention" 和 "mechanism" 的文本块
**语义检索**：找到包含 "self-attention", "transformer", "attention layer" 等的文本块
**混合结果**：结合两者，既保证精确匹配，又包含相关概念

### 示例 2：概念性查询

**查询**："novel approach to image generation"

**关键词检索**：可能找不到（因为 "novel" 可能不在文本中）
**语义检索**：能找到描述 "new method", "innovative approach" 等的文本块
**混合结果**：语义检索的结果被保留，提供相关上下文

## 性能对比

| 指标 | Simple RAG | Embedding RAG | Hybrid RAG |
|------|-----------|---------------|------------|
| 精确匹配 | ✅ 高 | ❌ 低 | ✅ 高 |
| 语义理解 | ❌ 低 | ✅ 高 | ✅ 高 |
| 召回率 | ❌ 低 | ✅ 高 | ✅✅ 最高 |
| 精确率 | ✅ 中 | ✅ 高 | ✅✅ 最高 |
| 构建时间 | 快 | 中等 | 中等 |
| 检索时间 | 快 | 快 | 中等（需要两次检索） |

## 代码结构

```python
class HybridRAG:
    def __init__(self, keyword_weight=0.3, semantic_weight=0.7, ...):
        self.keyword_rag = SimpleRAG(...)
        self.semantic_rag = EmbeddingRAG(...)
        self.keyword_weight = keyword_weight
        self.semantic_weight = semantic_weight
    
    def retrieve_relevant_chunks(self, paper_text, query, top_k=5):
        # 1. 关键词检索
        keyword_results = self.keyword_rag.retrieve_relevant_chunks(...)
        
        # 2. 语义检索
        semantic_results = self.semantic_rag.retrieve_relevant_chunks(...)
        
        # 3. 合并和加权
        # 4. 返回 top-k
```

## 集成方式

混合 RAG 已集成到 Pipeline 中：

1. **Pipeline 初始化**：根据 `method="hybrid"` 创建 HybridRAG
2. **索引管理**：自动构建 Embedding RAG 的索引
3. **Verification Agent**：自动识别 HybridRAG 并使用正确的接口

## 测试建议

可以对比三种方法的检索效果：

```python
# 测试 Simple RAG
config['rag']['method'] = 'simple'
result1 = pipeline.step2_verification("paper_19076")

# 测试 Embedding RAG
config['rag']['method'] = 'embedding'
result2 = pipeline.step2_verification("paper_19076")

# 测试 Hybrid RAG
config['rag']['method'] = 'hybrid'
result3 = pipeline.step2_verification("paper_19076")

# 对比验证结果的准确性
```

## 总结

混合 RAG 通过结合关键词匹配和语义检索，实现了：
- ✅ **更高的召回率**：能找到更多相关文本
- ✅ **更高的精确率**：两种方法都找到的文本更可靠
- ✅ **灵活的配置**：可根据场景调整权重
- ✅ **向后兼容**：可以随时切换回单一方法

这是目前推荐的 RAG 实现方式，能够充分利用两种方法的优势。

