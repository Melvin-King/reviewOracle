# 两种 RAG 的集成方式说明

## 集成架构

系统通过**策略模式（Strategy Pattern）**集成两种 RAG 实现，允许在运行时动态切换。

## 核心设计

### 1. 统一的接口抽象

两种 RAG 都实现了相同的接口方法：

```python
class RAGInterface:
    def get_context(self, query: str, top_k: int = 5) -> str:
        """获取相关上下文"""
        pass
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """检索相关块"""
        pass
```

**关键差异**：
- `SimpleRAG.get_context(paper_text, query, top_k)` - 需要传入 paper_text
- `EmbeddingRAG.get_context(query, top_k)` - 不需要 paper_text（已构建索引）

### 2. Pipeline 中的动态选择

在 `src/pipeline.py` 的 `__init__` 方法中：

```python
# 初始化 RAG 和 Verification Agent
rag_config = self.config.get('rag', {})
rag_method = rag_config.get('method', 'simple')  # 从配置读取

if rag_method == 'embedding':
    # 使用基于 Embedding 的 RAG
    embedding_model = rag_config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
    rag = EmbeddingRAG(
        model_name=embedding_model,
        chunk_size=rag_config.get('chunk_size', 500),
        chunk_overlap=rag_config.get('chunk_overlap', 50)
    )
    print(f"[INFO] Using Embedding RAG with model: {embedding_model}")
else:
    # 使用简单的关键词匹配 RAG
    rag = SimpleRAG(
        chunk_size=rag_config.get('chunk_size', 500),
        chunk_overlap=rag_config.get('chunk_overlap', 50)
    )
    print(f"[INFO] Using Simple RAG (keyword-based)")

self.rag = rag  # 保存引用
self.verification_agent = VerificationAgent(self.llm_client, rag)
```

**设计要点**：
- 根据配置文件动态选择实现
- 两种实现都传给同一个 `VerificationAgent`
- Agent 不需要知道具体是哪种实现

### 3. Verification Agent 中的适配

在 `src/agents/verification_agent.py` 的 `verify_claim` 方法中：

```python
def verify_claim(self, claim: Dict, paper_text: str = None) -> Dict:
    # ... 构建查询 ...
    
    # 使用 RAG 检索相关段落
    # 检查 RAG 类型以使用正确的接口
    from ..utils.embedding_rag import EmbeddingRAG
    if isinstance(self.rag, EmbeddingRAG):
        # Embedding RAG: 不需要传入 paper_text（已构建索引）
        context = self.rag.get_context(query, top_k=5)
    else:
        # Simple RAG: 需要传入 paper_text
        context = self.rag.get_context(paper_text, query, top_k=5)
```

**设计要点**：
- 使用 `isinstance` 检查 RAG 类型
- 根据类型调用不同的接口
- `paper_text` 参数对 EmbeddingRAG 是可选的

### 4. 索引管理

在 `step2_verification` 方法中处理 Embedding RAG 的索引：

```python
# 如果是 Embedding RAG，构建或加载索引
if isinstance(self.rag, EmbeddingRAG):
    rag_config = self.config.get('rag', {})
    index_path = rag_config.get('index_path')
    use_cache = rag_config.get('use_cache', True)
    
    if index_path and use_cache:
        # 尝试加载已保存的索引
        paper_index_path = f"{index_path}/{paper_id}"
        try:
            if Path(f"{paper_index_path}.index").exists():
                print(f"[RAG] Loading cached index for {paper_id}...")
                self.rag.load_index(paper_index_path)
            else:
                print(f"[RAG] Building new index for {paper_id}...")
                self.rag.build_index(paper_text, save_path=paper_index_path)
        except Exception as e:
            print(f"[WARNING] Failed to load/save index: {e}, building in memory...")
            self.rag.build_index(paper_text)
    else:
        # 在内存中构建索引（不保存）
        if not self.rag.is_built():
            print(f"[RAG] Building index for {paper_id}...")
            self.rag.build_index(paper_text)
```

**设计要点**：
- 只在需要时构建索引（首次使用 EmbeddingRAG）
- 支持索引缓存（避免重复构建）
- 优雅降级（如果缓存失败，在内存中构建）

## 类图关系

```
┌─────────────────┐
│  EVWPipeline    │
│                 │
│  - rag: RAG     │──┐
│  - config       │  │
└─────────────────┘  │
                     │ 持有
                     ▼
         ┌───────────────────────┐
         │  VerificationAgent    │
         │                       │
         │  - rag: RAG           │
         │  - llm_client         │
         └───────────────────────┘
                     │ 使用
                     │
         ┌───────────┴───────────┐
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│   SimpleRAG     │    │  EmbeddingRAG    │
│                 │    │                  │
│ + get_context() │    │ + get_context()  │
│ + chunk_text()  │    │ + build_index()  │
│ + extract_      │    │ + load_index()   │
│   keywords()    │    │ + retrieve_      │
└─────────────────┘    │   relevant_      │
                       │   chunks()       │
                       └──────────────────┘
```

## 配置驱动的切换

通过修改 `config.yaml` 即可切换：

```yaml
# 使用 Embedding RAG
rag:
  method: "embedding"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  use_cache: true
  index_path: "data/processed/rag_indices"

# 或使用 Simple RAG
rag:
  method: "simple"
```

**优势**：
- 无需修改代码
- 运行时切换
- 易于测试和对比

## 接口兼容性处理

### 问题：接口签名不同

- `SimpleRAG.get_context(paper_text, query, top_k)`
- `EmbeddingRAG.get_context(query, top_k)`

### 解决方案：运行时适配

```python
# 在 VerificationAgent 中
if isinstance(self.rag, EmbeddingRAG):
    context = self.rag.get_context(query, top_k=5)  # 不需要 paper_text
else:
    context = self.rag.get_context(paper_text, query, top_k=5)  # 需要 paper_text
```

**设计考虑**：
- 不强制统一接口（保持各自最优设计）
- 在调用处适配（最小化影响）
- 类型检查确保正确调用

## 扩展性

### 添加新的 RAG 实现

1. 创建新类（如 `HybridRAG`）
2. 实现 `get_context` 方法
3. 在 Pipeline 中添加选择逻辑：

```python
elif rag_method == 'hybrid':
    rag = HybridRAG(...)
```

4. 在 VerificationAgent 中添加类型检查：

```python
elif isinstance(self.rag, HybridRAG):
    context = self.rag.get_context(...)
```

## 实际使用流程

### 使用 Simple RAG

```python
# config.yaml
rag:
  method: "simple"

# 运行
pipeline = EVWPipeline()  # 自动使用 SimpleRAG
pipeline.step2_verification("paper_19076")
```

### 使用 Embedding RAG

```python
# config.yaml
rag:
  method: "embedding"
  use_cache: true

# 首次运行
pipeline = EVWPipeline()  # 自动使用 EmbeddingRAG
pipeline.step2_verification("paper_19076")  # 构建索引

# 后续运行
pipeline.step2_verification("paper_19076")  # 加载缓存索引
```

## 测试两种实现

可以轻松对比两种实现：

```python
# 测试 Simple RAG
config['rag']['method'] = 'simple'
pipeline1 = EVWPipeline()
result1 = pipeline1.step2_verification("paper_19076")

# 测试 Embedding RAG
config['rag']['method'] = 'embedding'
pipeline2 = EVWPipeline()
result2 = pipeline2.step2_verification("paper_19076")

# 对比结果
compare_results(result1, result2)
```

## 总结

集成方式的核心特点：

1. **策略模式**：运行时选择实现
2. **配置驱动**：通过配置文件切换
3. **接口适配**：在调用处处理接口差异
4. **向后兼容**：保留 Simple RAG 作为备选
5. **易于扩展**：可以轻松添加新的 RAG 实现

这种设计既保持了代码的灵活性，又确保了系统的可维护性。

