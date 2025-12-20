# 两种 RAG 集成方式总结

## 测试结果

✅ **Embedding RAG 测试成功**：
- 索引构建：163 个文本块，384 维向量
- 索引保存：成功保存到 `data/processed/rag_indices/paper_19076`
- 检索功能：正常工作，能找到语义相关的文本块

## 集成架构

### 1. 策略模式实现

在 `src/pipeline.py` 中，根据配置动态选择 RAG 实现：

```python
# 从配置读取方法
rag_method = rag_config.get('method', 'simple')

if rag_method == 'embedding':
    rag = EmbeddingRAG(...)  # 语义检索
else:
    rag = SimpleRAG(...)     # 关键词匹配

# 统一传给 VerificationAgent
self.verification_agent = VerificationAgent(self.llm_client, rag)
```

### 2. 接口适配

在 `src/agents/verification_agent.py` 中，根据 RAG 类型调用不同接口：

```python
# 检查 RAG 类型
if isinstance(self.rag, EmbeddingRAG):
    # Embedding RAG: 不需要 paper_text（已构建索引）
    context = self.rag.get_context(query, top_k=5)
else:
    # Simple RAG: 需要 paper_text
    context = self.rag.get_context(paper_text, query, top_k=5)
```

### 3. 索引管理

在 `step2_verification` 中自动处理索引：

```python
if isinstance(self.rag, EmbeddingRAG):
    # 检查是否有缓存
    if Path(f"{index_path}.index").exists():
        self.rag.load_index(index_path)  # 加载缓存
    else:
        self.rag.build_index(paper_text, save_path=index_path)  # 构建并保存
```

## 关键设计点

1. **统一接口抽象**：两种 RAG 都实现 `get_context()` 方法
2. **运行时选择**：通过配置动态选择，无需修改代码
3. **类型检查适配**：在调用处处理接口差异
4. **自动索引管理**：首次构建，后续使用缓存

## 切换方式

只需修改 `config.yaml`：

```yaml
# 使用 Embedding RAG（推荐）
rag:
  method: "embedding"

# 或使用 Simple RAG
rag:
  method: "simple"
```

## 文件结构

```
src/
├── utils/
│   ├── rag.py              # SimpleRAG（关键词匹配）
│   └── embedding_rag.py    # EmbeddingRAG（语义检索）
├── agents/
│   └── verification_agent.py  # 适配两种 RAG
└── pipeline.py             # 动态选择 RAG
```

## 优势

- ✅ **向后兼容**：保留 Simple RAG 作为备选
- ✅ **易于切换**：配置文件即可切换
- ✅ **性能优化**：Embedding RAG 支持索引缓存
- ✅ **易于扩展**：可以轻松添加新的 RAG 实现

