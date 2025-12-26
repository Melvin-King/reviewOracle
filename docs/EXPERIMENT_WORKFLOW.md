# 实验运行流程与文件说明

## 完整实验流程概览

```
输入数据准备
    ↓
Step 1: 观点提取 (Extraction)
    ↓
Step 2: 事实验证 (Verification)
    ↓
Step 3: 权重计算 (Weighting)
    ↓
Step 4: 报告合成 (Synthesis)
    ↓
结果分析与统计
```

---

## 一、输入文件准备

### 1.1 论文PDF文件

**位置**：
- NIPS论文：`data/raw/papers/{paper_id}.pdf`
- ICLR 2024 Accepted：`data/raw/iclr2024/papers/accepted/{paper_id}.pdf`
- ICLR 2024 Rejected：`data/raw/iclr2024/papers/rejected/{paper_id}.pdf`

**示例**：
```
data/raw/papers/paper_19076.pdf
data/raw/iclr2024/papers/accepted/eepoE7iLpL.pdf
data/raw/iclr2024/papers/rejected/ApjY32f3Xr.pdf
```

### 1.2 评审JSON文件

**位置**：
- NIPS评审：`data/raw/reviews/{paper_id}_reviews.json`
- ICLR 2024评审：`data/raw/iclr2024/reviews/{paper_id}_reviews.json`

**格式**：
```json
[
  {
    "id": "review_id",
    "content": {
      "review": "评审文本内容...",
      "rating": "8"
    },
    "signatures": ["~Reviewer1"]
  }
]
```

**示例**：
```
data/raw/reviews/paper_19076_reviews.json
data/raw/iclr2024/reviews/eepoE7iLpL_reviews.json
```

### 1.3 配置文件

**位置**：`config.yaml`

**主要内容**：
- LLM配置（provider, model, temperature）
- RAG配置（method, use_reranking, embedding_model等）
- 权重计算配置（alpha, beta）
- 合成配置（accept_threshold, topics等）

---

## 二、实验步骤与调用文件

### Step 1: 观点提取 (Extraction)

**调用脚本**：
```bash
# 单篇论文
python run_step1_extraction.py

# 批量处理（需要修改脚本中的paper_ids列表）
python run_step1_extraction.py
```

**输入文件**：
- `data/raw/reviews/{paper_id}_reviews.json` - 评审JSON文件

**输出文件**：
- `data/processed/extracted/{paper_id}_claims.json` - 结构化观点

**输出格式**：
```json
[
  {
    "id": "R1-C1",
    "topic": "Experiments",
    "sentiment": "Positive",
    "statement": "The experimental results show significant improvements.",
    "substantiation_type": "Specific_Citation",
    "substantiation_content": "Table 1, Section 4.2"
  }
]
```

**处理时间**：~2-5秒/论文

---

### Step 2: 事实验证 (Verification)

**调用脚本**：
```bash
# 单篇论文
python run_step2_verification.py

# 批量处理
python run_step2_batch.py

# ICLR 2024批量处理
python run_iclr_pipeline_steps.py  # 包含Step 1, 2, 3
```

**输入文件**：
- `data/processed/extracted/{paper_id}_claims.json` - Step 1输出
- `data/raw/papers/{paper_id}.pdf` - 论文PDF（或已解析的文本缓存）

**输出文件**：
- `data/results/verifications/{paper_id}_verified.json` - 验证结果
- `data/processed/rag_indices/{paper_id}.*` - RAG索引缓存（可选）

**输出格式**：
```json
[
  {
    "id": "R1-C1",
    "verification_result": "True",
    "verification_reason": "Paper explicitly states...",
    "confidence": 0.95
  }
]
```

**处理时间**：~30-60秒/论文（取决于claims数量）

**关键特性**：
- 自动识别相关section并过滤
- 支持稀疏检索、稠密检索、混合检索
- 支持重排序优化

---

### Step 3: 权重计算 (Weighting)

**调用脚本**：
```bash
# 单篇论文
python run_step3_weighting.py

# 批量处理
python run_step3_batch.py

# ICLR 2024批量处理
python run_iclr_pipeline_steps.py  # 包含Step 1, 2, 3
```

**输入文件**：
- `data/processed/extracted/{paper_id}_claims.json` - Step 1输出
- `data/results/verifications/{paper_id}_verified.json` - Step 2输出

**输出文件**：
- `data/results/weights/{paper_id}_weights.json` - 评审者权重

**输出格式**：
```json
{
  "R1": {
    "weight": 0.85,
    "hollowness": 0.10,
    "hallucination": 0.05,
    "num_claims": 10,
    "num_false": 1
  }
}
```

**处理时间**：<1秒/论文

---

### Step 4: 报告合成 (Synthesis)

**调用脚本**：
```bash
# 单篇论文
python run_step4_synthesis.py

# 批量处理
python run_step4_batch.py
```

**输入文件**：
- `data/processed/extracted/{paper_id}_claims.json` - Step 1输出
- `data/results/verifications/{paper_id}_verified.json` - Step 2输出
- `data/results/weights/{paper_id}_weights.json` - Step 3输出

**输出文件**：
- `data/results/synthesis/{paper_id}_report.md` - Meta-Review报告

**输出格式**：Markdown格式，包含：
- 评审者可信度权重
- 各主题评分（10分制）
- 加权投票结果
- 最终决策（ACCEPT/REJECT）

**处理时间**：~5-10秒/论文

---

## 三、完整流程运行

### 3.1 使用Pipeline类（推荐）

**脚本**：`scripts/run_pipeline.py` 或直接使用Python

```python
from src.pipeline import EVWPipeline

# 初始化
pipeline = EVWPipeline(config_path="config.yaml")

# 运行完整流程
pipeline.run_pipeline("paper_19076")

# 或分步运行
claims = pipeline.step1_extraction("paper_19076")
verifications = pipeline.step2_verification("paper_19076")
weights = pipeline.step3_weighting("paper_19076")
report = pipeline.step4_synthesis("paper_19076")
```

### 3.2 使用命令行脚本

```bash
# 运行完整流程
python scripts/run_pipeline.py --paper-id paper_19076

# 只运行特定步骤
python scripts/run_pipeline.py --paper-id paper_19076 --step 2
```

### 3.3 ICLR 2024批量处理

```bash
# 运行Step 1, 2, 3（批量）
python run_iclr_pipeline_steps.py
```

---

## 四、结果分析与统计

### 4.1 预测准确率分析

**脚本**：`calculate_prediction_accuracy.py`

**输入**：
- `data/results/verifications/{paper_id}_verified.json` - 所有论文的验证结果
- `data/results/weights/{paper_id}_weights.json` - 所有论文的权重结果
- 论文PDF位置（用于确定ground truth：accepted/rejected）

**输出**：
- `data/results/iclr2024_prediction_accuracy.json` - 预测准确率结果

**运行**：
```bash
python calculate_prediction_accuracy.py
```

### 4.2 详细统计分析

**脚本**：`analyze_iclr_results.py`

**输入**：
- `data/results/iclr2024_pipeline_results.json` - Pipeline结果汇总

**输出**：
- `data/results/iclr2024_statistics.json` - 详细统计信息

**运行**：
```bash
python analyze_iclr_results.py
```

### 4.3 对比分析报告

**脚本**：`generate_final_statistics.py`

**输入**：
- `data/results/iclr2024_pipeline_results.json`

**输出**：
- `data/results/iclr2024_comparison_report.json` - Accepted vs Rejected对比报告

**运行**：
```bash
python generate_final_statistics.py
```

### 4.4 详细预测分析

**脚本**：`detailed_prediction_analysis.py`

**输入**：
- 所有论文的验证和权重结果

**输出**：
- 控制台输出：每篇论文的详细分数和预测结果

**运行**：
```bash
python detailed_prediction_analysis.py
```

---

## 五、完整文件结构

```
data/
├── raw/                          # 原始输入数据
│   ├── papers/                   # NIPS论文PDF
│   │   └── {paper_id}.pdf
│   ├── reviews/                  # NIPS评审JSON
│   │   └── {paper_id}_reviews.json
│   └── iclr2024/                 # ICLR 2024数据
│       ├── papers/
│       │   ├── accepted/
│       │   │   └── {paper_id}.pdf
│       │   └── rejected/
│       │       └── {paper_id}.pdf
│       └── reviews/
│           └── {paper_id}_reviews.json
│
├── processed/                    # 中间处理结果
│   ├── extracted/                # Step 1输出
│   │   └── {paper_id}_claims.json
│   ├── papers/                   # 解析后的论文文本（缓存）
│   │   └── {paper_id}.txt
│   └── rag_indices/              # RAG索引缓存（可选）
│       └── {paper_id}.*
│
└── results/                      # 最终结果
    ├── verifications/            # Step 2输出
    │   └── {paper_id}_verified.json
    ├── weights/                   # Step 3输出
    │   └── {paper_id}_weights.json
    ├── synthesis/                 # Step 4输出
    │   └── {paper_id}_report.md
    └── iclr2024_*.json           # 统计分析结果
```

---

## 六、快速开始示例

### 示例1：处理单篇NIPS论文

```bash
# 1. 确保输入文件存在
# data/raw/papers/paper_19076.pdf
# data/raw/reviews/paper_19076_reviews.json

# 2. 运行完整流程
python run_step1_extraction.py      # 修改脚本中的PAPER_ID
python run_step2_verification.py    # 修改脚本中的PAPER_ID
python run_step3_weighting.py      # 修改脚本中的PAPER_ID
python run_step4_synthesis.py      # 修改脚本中的PAPER_ID

# 3. 查看结果
# data/results/synthesis/paper_19076_report.md
```

### 示例2：批量处理ICLR 2024论文

```bash
# 1. 确保已下载论文和评审
# data/raw/iclr2024/papers/accepted/*.pdf
# data/raw/iclr2024/papers/rejected/*.pdf
# data/raw/iclr2024/reviews/*_reviews.json

# 2. 运行Step 1, 2, 3
python run_iclr_pipeline_steps.py

# 3. 运行Step 4（如果需要）
python run_step4_batch.py  # 需要修改脚本中的paper_ids

# 4. 统计分析
python calculate_prediction_accuracy.py
python generate_final_statistics.py
```

### 示例3：使用Pipeline API

```python
from src.pipeline import EVWPipeline

pipeline = EVWPipeline(config_path="config.yaml")

# 单篇论文完整流程
paper_id = "paper_19076"
pipeline.run_pipeline(paper_id)

# 或分步执行
claims = pipeline.step1_extraction(paper_id)
verifications = pipeline.step2_verification(paper_id)
weights = pipeline.step3_weighting(paper_id)
report = pipeline.step4_synthesis(paper_id)
```

---

## 七、注意事项

1. **文件命名**：确保paper_id在所有步骤中保持一致
2. **依赖顺序**：Step 2依赖Step 1，Step 3依赖Step 1和2，Step 4依赖Step 1、2、3
3. **缓存机制**：Step 2会缓存RAG索引，重复运行会更快
4. **配置检查**：运行前检查`config.yaml`中的LLM API key和模型配置
5. **错误处理**：批量处理时，单个论文失败不会中断整个流程

---

## 八、常见问题

**Q: 如何查看中间结果？**
A: 所有中间结果都保存在`data/processed/`和`data/results/`目录下，可以直接查看JSON文件。

**Q: 如何重新运行某个步骤？**
A: 直接删除对应的输出文件，然后重新运行该步骤的脚本。

**Q: 如何批量处理多篇论文？**
A: 修改脚本中的paper_ids列表，或使用批量处理脚本（如`run_step2_batch.py`）。

**Q: RAG索引在哪里？**
A: 默认保存在`data/processed/rag_indices/`，可以删除以强制重建。

**Q: 如何更改配置？**
A: 修改`config.yaml`文件，然后重新初始化Pipeline。


