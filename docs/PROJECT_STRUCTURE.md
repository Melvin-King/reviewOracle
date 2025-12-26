# E-V-W Evaluation Stack 项目结构设计

## 目录结构

```
paperreview/
├── README.md                          # 项目说明文档（根目录）
├── requirements.txt                   # Python 依赖包
├── config.yaml                        # 配置文件（API keys, 参数等）
│
├── data/                              # 数据目录
│   ├── raw/                           # 原始数据
│   │   ├── papers/                    # 下载的论文 PDF
│   │   │   ├── paper_001.pdf
│   │   │   ├── paper_002.pdf
│   │   │   └── paper_003.pdf
│   │   └── reviews/                   # 下载的 review 文本
│   │       ├── paper_001_reviews.json
│   │       ├── paper_002_reviews.json
│   │       └── paper_003_reviews.json
│   ├── processed/                     # 处理后的数据
│   │   ├── papers/                    # 解析后的论文文本
│   │   │   ├── paper_001.txt
│   │   │   ├── paper_002.txt
│   │   │   └── paper_003.txt
│   │   └── extracted/                 # Step 1 提取的结构化观点
│   │       ├── paper_001_claims.json
│   │       ├── paper_002_claims.json
│   │       └── paper_003_claims.json
│   └── results/                        # 最终结果
│       ├── verifications/             # Step 2 验证结果
│       │   ├── paper_001_verified.json
│       │   ├── paper_002_verified.json
│       │   └── paper_003_verified.json
│       ├── weights/                   # Step 3 权重计算结果
│       │   ├── paper_001_weights.json
│       │   ├── paper_002_weights.json
│       │   └── paper_003_weights.json
│       └── synthesis/                 # Step 4 最终报告
│           ├── paper_001_report.md
│           ├── paper_002_report.md
│           └── paper_003_report.md
│
├── src/                                # 源代码目录
│   ├── __init__.py
│   │
│   ├── data/                           # 数据下载和处理模块
│   │   ├── __init__.py
│   │   ├── downloader.py              # 从 NIPS 2024 下载论文和 review
│   │   ├── pdf_parser.py               # PDF 解析工具
│   │   └── data_loader.py              # 数据加载工具
│   │
│   ├── agents/                         # Agent 实现
│   │   ├── __init__.py
│   │   ├── extraction_agent.py        # Step 1: 结构化提取 Agent
│   │   ├── verification_agent.py      # Step 2: 事实验证 Agent
│   │   ├── weighting_agent.py         # Step 3: 偏差计算与加权 Agent
│   │   └── synthesis_agent.py         # Step 4: 合成决策 Agent
│   │
│   ├── utils/                          # 工具函数
│   │   ├── __init__.py
│   │   ├── llm_client.py               # LLM API 客户端封装
│   │   ├── rag.py                      # RAG 检索增强生成工具
│   │   ├── text_processing.py         # 文本处理工具
│   │   └── metrics.py                  # 计算指标的工具函数
│   │
│   └── pipeline.py                     # 主流程编排
│
├── tests/                              # 测试文件
│   ├── __init__.py
│   ├── test_extraction.py
│   ├── test_verification.py
│   └── test_weighting.py
│
└── scripts/                            # 脚本文件
    ├── download_data.py                # 数据下载脚本
    ├── run_pipeline.py                 # 运行完整流程
    └── visualize_results.py            # 结果可视化
```

## 各模块功能说明

### 1. 数据模块 (`src/data/`)

#### `downloader.py`
- **功能**：从 NIPS 2024 下载论文和 review
- **主要函数**：
  - `download_nips_papers(year, num_papers=3)`: 下载指定数量的论文
  - `download_reviews(paper_id)`: 下载对应论文的 review
  - `save_paper(pdf_content, paper_id)`: 保存论文 PDF
  - `save_reviews(reviews_data, paper_id)`: 保存 review 数据
- **数据源**：OpenReview API 或 NIPS 官方网站

#### `pdf_parser.py`
- **功能**：解析 PDF 文件，提取文本内容
- **主要函数**：
  - `parse_pdf(pdf_path)`: 解析 PDF 并提取文本
  - `extract_sections(pdf_text)`: 提取论文章节结构
  - `clean_text(text)`: 清理文本（去除特殊字符、格式化等）

#### `data_loader.py`
- **功能**：统一的数据加载接口
- **主要函数**：
  - `load_paper_text(paper_id)`: 加载论文文本
  - `load_reviews(paper_id)`: 加载 review 数据
  - `load_claims(paper_id)`: 加载已提取的观点

### 2. Agent 模块 (`src/agents/`)

#### `extraction_agent.py` (Step 1)
- **功能**：结构化提取 Review 中的观点
- **主要类/函数**：
  - `ExtractionAgent`: 主 Agent 类
  - `extract_claims(review_text)`: 提取原子观点
  - `classify_substantiation(claim)`: 分类证据类型
- **输出格式**：符合 [read.md](read.md) 中定义的 JSON 格式

#### `verification_agent.py` (Step 2)
- **功能**：验证观点是否与论文一致
- **主要类/函数**：
  - `VerificationAgent`: 主 Agent 类
  - `verify_claim(claim, paper_text)`: 验证单个观点
  - `rag_search(claim, paper_text)`: RAG 检索相关段落
- **依赖**：RAG 工具 (`utils/rag.py`)

#### `weighting_agent.py` (Step 3)
- **功能**：计算 Reviewer 的可信度权重
- **主要类/函数**：
  - `WeightingAgent`: 主 Agent 类
  - `calculate_hollowness(reviewer_claims)`: 计算空洞指数
  - `calculate_hallucination(reviewer_claims)`: 计算幻觉指数
  - `calculate_weight(reviewer_id, claims, verifications)`: 计算最终权重
- **算法**：实现 [read.md](read.md) 中的权重计算公式

#### `synthesis_agent.py` (Step 4)
- **功能**：生成最终的 Meta-Review 报告
- **主要类/函数**：
  - `SynthesisAgent`: 主 Agent 类
  - `filter_false_claims(claims, verifications)`: 过滤错误观点
  - `weighted_voting(topic, claims, weights)`: 加权投票
  - `generate_report(paper_id, all_data)`: 生成最终报告

### 3. 工具模块 (`src/utils/`)

#### `llm_client.py`
- **功能**：封装 LLM API 调用（OpenAI, Anthropic 等）
- **主要函数**：
  - `call_llm(prompt, model, temperature)`: 统一 LLM 调用接口
  - `batch_call_llm(prompts)`: 批量调用

#### `rag.py`
- **功能**：RAG 检索增强生成
- **主要函数**：
  - `build_vector_store(paper_text)`: 构建向量数据库
  - `retrieve_relevant_chunks(query, top_k)`: 检索相关段落
  - `generate_with_context(query, context)`: 基于上下文生成

#### `text_processing.py`
- **功能**：文本处理工具函数
- **主要函数**：
  - `split_into_sentences(text)`: 分句
  - `extract_citations(text)`: 提取引用
  - `normalize_text(text)`: 文本标准化

#### `metrics.py`
- **功能**：计算各种指标
- **主要函数**：
  - `calculate_sentiment_score(sentiment)`: 情感分数转换
  - `aggregate_topic_scores(topic_claims, weights)`: 聚合主题分数

### 4. 主流程 (`src/pipeline.py`)
- **功能**：编排整个 E-V-W 流程
- **主要函数**：
  - `run_evw_pipeline(paper_id)`: 运行完整流程
  - `step1_extraction(paper_id)`: 执行 Step 1
  - `step2_verification(paper_id)`: 执行 Step 2
  - `step3_weighting(paper_id)`: 执行 Step 3
  - `step4_synthesis(paper_id)`: 执行 Step 4

### 5. 配置文件 (`config.yaml`)
```yaml
# API 配置
llm:
  provider: "openai"  # 或 "anthropic"
  api_key: "your-api-key"
  model: "gpt-4"
  temperature: 0.3

# RAG 配置
rag:
  embedding_model: "text-embedding-3-small"
  top_k: 5
  chunk_size: 500
  chunk_overlap: 50

# 权重计算参数
weighting:
  alpha: 0.5  # Hollowness 惩罚系数
  beta: 0.5   # Hallucination 惩罚系数

# 数据源配置
data_source:
  nips_year: 2024
  num_papers: 3
  download_path: "data/raw"

# 决策阈值
synthesis:
  accept_threshold: 0.6
```

### 6. 脚本文件 (`scripts/`)

#### `download_data.py`
- 独立的数据下载脚本
- 用法：`python scripts/download_data.py --num-papers 3`

#### `run_pipeline.py`
- 运行完整流程的主脚本
- 用法：`python scripts/run_pipeline.py --paper-id paper_001`

#### `visualize_results.py`
- 结果可视化脚本（可选）
- 生成图表展示权重、分数等

## 技术栈建议

- **PDF 解析**：PyPDF2, pdfplumber, 或 pymupdf
- **LLM API**：OpenAI, Anthropic Claude
- **向量数据库**：FAISS, Chroma, 或简单的 in-memory 向量搜索
- **文本处理**：spaCy, NLTK
- **数据存储**：JSON 文件（简单场景）或 SQLite（复杂场景）

## 开发顺序建议

1. **Phase 1**: 数据下载和处理
   - 实现 `downloader.py` 和 `pdf_parser.py`
   - 测试下载 3 篇 NIPS 2024 论文

2. **Phase 2**: Step 1 - 结构化提取
   - 实现 `extraction_agent.py`
   - 测试提取 review 中的观点

3. **Phase 3**: Step 2 - 事实验证
   - 实现 `verification_agent.py` 和 `rag.py`
   - 测试观点验证功能

4. **Phase 4**: Step 3 & 4 - 权重计算和合成
   - 实现 `weighting_agent.py` 和 `synthesis_agent.py`
   - 完成完整流程

5. **Phase 5**: 优化和测试
   - 添加错误处理
   - 性能优化
   - 编写测试用例

