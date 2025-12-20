# E-V-W 评估栈 Pipeline 文档

## 概述

E-V-W (Extraction-Verification-Weighting) 评估栈是一个系统化的学术论文评审评估框架。它通过四个独立的步骤处理评审，每个步骤由专门的 Agent 处理，以生成客观且基于证据的 Meta-Review。

## Pipeline 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    E-V-W 评估流程                                │
└─────────────────────────────────────────────────────────────────┘

输入: 论文 PDF + 评审 (JSON)
    │
    ├─► 步骤 1: 提取 Agent
    │   └─► 输出: 结构化观点 (JSON)
    │
    ├─► 步骤 2: 验证 Agent
    │   └─► 输出: 验证结果 (JSON)
    │
    ├─► 步骤 3: 加权 Agent
    │   └─► 输出: 评审者权重 (JSON)
    │
    └─► 步骤 4: 合成 Agent
        └─► 输出: Meta-Review 报告 (Markdown)
```

## 逐步流程说明

### 步骤 1: 结构化提取 Agent

**文件**: `src/agents/extraction_agent.py`

**目的**: 从评审文本中提取原子观点并分类证据类型。

**功能**:
1. 接收原始评审文本作为输入（**不读取论文**）
2. 使用 LLM 将评审拆解为原子观点
3. 对每个观点提取：
   - `id`: 唯一标识符（如 "R1-C1"）
   - `topic`: 主题分类（Novelty, Experiments, Writing, Significance, Reproducibility）
   - `sentiment`: 情感（Positive, Negative, Neutral）
   - `statement`: 观点陈述文本
   - `substantiation_type`: 证据质量分类
     - `Specific_Citation`: 有具体证据或引用
     - `Vague`: 有模糊或不明确的证据
     - `None`: 完全没有证据
   - `substantiation_content`: 证据内容（如果有）

**核心逻辑**:
- 分别处理每个评审
- 使用结构化提示确保一致的 JSON 输出
- 早期分类证据质量以识别潜在偏差

**输出格式**:
```json
[
  {
    "id": "R1-C1",
    "topic": "Novelty",
    "sentiment": "Positive",
    "statement": "This idea is natural and novel.",
    "substantiation_type": "Specific_Citation",
    "substantiation_content": "It successfully solves mathematical premises violation..."
  }
]
```

**实际输出示例**:
- 对于 `paper_19076`: 从 4 个评审者中提取了 38 个观点

---

### 步骤 2: 事实验证 Agent

**文件**: `src/agents/verification_agent.py`

**目的**: 验证观点是否与论文实际内容一致。

**功能**:
1. 加载论文文本（PDF 解析为文本）
2. 只处理有证据的观点（`substantiation_type != None`）
3. 对每个观点：
   - 使用 RAG（检索增强生成）查找相关论文段落
   - 将观点 + 论文上下文发送给 LLM 进行验证
   - 判断观点是：
     - `True`: 完全被论文支持
     - `False`: 与论文矛盾或不支持
     - `Partially_True`: 部分正确但有不准确之处
4. 生成验证原因和置信度分数

**RAG 组件** (`src/utils/rag.py`):
- 将论文文本分割成可管理的块
- 从观点中提取关键词
- 基于关键词匹配检索 top-k 最相关的文本块
- 为 LLM 提供上下文进行验证

**核心逻辑**:
- 只验证有证据的观点（过滤掉 `None` 类型）
- 使用客观的事实检查方法
- 为每个验证提供详细推理

**输出格式**:
```json
[
  {
    "id": "R1-C1",
    "verification_result": "Partially_True",
    "verification_reason": "The claim has both accurate and inaccurate elements...",
    "confidence": 0.85
  }
]
```

**实际输出示例**:
- 对于 `paper_19076`: 验证了 30 个观点（共 38 个）
  - True: 14 个
  - False: 5 个
  - Partially_True: 11 个
  - 平均置信度: 0.89

---

### 步骤 3: 偏差计算与加权 Agent

**文件**: `src/agents/weighting_agent.py`

**目的**: 基于客观指标计算每个评审者的可信度权重。

**功能**:
1. 按评审者分组观点
2. 对每个评审者计算两个偏差指数：

   **空洞指数 (Hollowness)**:
   - `substantiation_type == None` 的观点占比
   - 衡量有多少观点缺乏证据
   - 公式: `空洞指数 = (无证据观点数) / (总观点数)`

   **幻觉指数 (Hallucination)**:
   - 验证为 `False` 的观点占比
   - 衡量有多少有证据的观点是错误的
   - 公式: `幻觉指数 = (错误观点数) / (有证据观点数)`

3. 使用公式计算最终权重：
   ```
   权重(R) = 1.0 - (α × 空洞指数 + β × 幻觉指数)
   ```
   其中：
   - `α` = 空洞惩罚系数（默认: 0.5）
   - `β` = 幻觉惩罚系数（默认: 0.5）

**核心逻辑**:
- 数学方法（非基于 LLM）
- 透明计算：低权重 = 高偏差（要么空洞，要么幻觉）
- 权重范围: [0.0, 1.0]

**输出格式**:
```json
{
  "R1": {
    "weight": 0.478,
    "hollowness": 0.444,
    "hallucination": 0.6,
    "num_claims": 9,
    "num_claims_with_evidence": 5,
    "num_false_claims": 3
  }
}
```

**实际输出示例**:
- 对于 `paper_19076`: 计算了 4 个评审者的权重
  - R4: 1.000（完美：无空洞，无幻觉）
  - R2: 0.905（低空洞，低幻觉）
  - R3: 0.750（中等空洞，低幻觉）
  - R1: 0.478（高空洞，高幻觉）

---

### 步骤 4: Meta-Review 合成 Agent

**文件**: `src/agents/synthesis_agent.py`

**目的**: 使用加权投票生成最终的 Meta-Review 报告。

**功能**:
1. 过滤掉错误观点（`verification_result == False`）
2. 按主题分组剩余观点
3. 对每个主题进行加权投票：
   - 将情感转换为分数：Positive=+1.0, Negative=-1.0, Neutral=0.0
   - 计算加权贡献：`情感 × 评审者权重`
   - 求和所有贡献：`主题分数 = Σ(情感 × 权重)`
   - 按总权重归一化
4. 对每个主题做出决策：
   - `Accept`: 分数 ≥ 阈值（默认: 0.6）
   - `Reject`: 分数 ≤ -阈值
   - `Neutral`: 其他情况
5. 生成综合报告，包括：
   - 评审者可信度权重
   - 基于主题的评估和分数
   - 关键观点及其贡献
   - 总体评估和建议

**核心逻辑**:
- 只考虑已验证的观点（过滤错误观点）
- 加权投票确保可信的评审者有更大影响力
- 透明评分显示每个决策的原因

**输出格式**: Markdown 报告，包含以下部分：
- 评审者可信度权重
- 基于主题的评估（每个主题）
- 总体评估

**实际输出示例**:
- 对于 `paper_19076`:
  - Novelty（新颖性）: Accept (0.765)
  - Significance（重要性）: Accept (1.000)
  - Experiments（实验）: Neutral (0.169)
  - Writing（写作）: Neutral (-0.356)
  - Reproducibility（可复现性）: Reject (-0.775)
  - 总体: NEUTRAL / REVISE（中性/需要修改）

---

## 数据流转

```
data/raw/
├── papers/
│   └── paper_19076.pdf          # 输入: 论文 PDF
└── reviews/
    └── paper_19076_reviews.json # 输入: 评审

    ↓ 步骤 1: 提取

data/processed/
└── extracted/
    └── paper_19076_claims.json  # 输出: 结构化观点

    ↓ 步骤 2: 验证

data/results/
└── verifications/
    └── paper_19076_verified.json # 输出: 验证结果

    ↓ 步骤 3: 加权

data/results/
└── weights/
    └── paper_19076_weights.json # 输出: 评审者权重

    ↓ 步骤 4: 合成

data/results/
└── synthesis/
    └── paper_19076_report.md    # 最终输出: Meta-review
```

## 配置说明

Pipeline 通过 `config.yaml` 配置：

```yaml
llm:
  provider: "deepseek"  # 或 "openai", "anthropic"
  model: "deepseek-chat"
  temperature: 0.3

rag:
  chunk_size: 500
  chunk_overlap: 50
  top_k: 5

weighting:
  alpha: 0.5  # 空洞惩罚系数
  beta: 0.5   # 幻觉惩罚系数

synthesis:
  accept_threshold: 0.6
  topics: ["Novelty", "Experiments", "Writing", "Significance", "Reproducibility"]
```

## 运行 Pipeline

### 单独运行各步骤

```bash
# 步骤 1: 提取观点
python run_step1_extraction.py

# 步骤 2: 验证观点
python run_step2_verification.py

# 步骤 3: 计算权重
python run_step3_weighting.py

# 步骤 4: 生成报告
python run_step4_synthesis.py
```

### 完整流程

```python
from src.pipeline import EVWPipeline

pipeline = EVWPipeline()
result = pipeline.run_pipeline("paper_19076")
```

## 核心设计原则

1. **关注点分离**: 每个步骤独立，可以单独运行
2. **基于证据**: 只验证有证据的观点；过滤错误观点
3. **透明性**: 所有计算都是明确且可复现的
4. **客观性**: 使用数学公式进行加权，而非主观的 LLM 判断
5. **结构化输出**: 所有中间结果都保存为 JSON 以便检查

## 示例：paper_19076 的完整流程

1. **输入**: 
   - 4 个评审（R1-R4）
   - 1 篇论文 PDF

2. **步骤 1 输出**: 
   - 提取了 38 个观点
   - 证据类型已分类

3. **步骤 2 输出**: 
   - 验证了 30 个观点（8 个无证据）
   - 14 个 True，5 个 False，11 个 Partially_True

4. **步骤 3 输出**: 
   - 计算了 4 个评审者权重
   - R1: 0.478（低可信度）
   - R4: 1.000（高可信度）

5. **步骤 4 输出**: 
   - 最终 Meta-Review 报告
   - 主题分数和决策
   - 总体建议: NEUTRAL / REVISE

## 方法优势

1. **解决不一致问题**: 步骤 2 验证观点与论文事实的一致性
2. **解决偏差问题**: 步骤 3 惩罚高空洞或高幻觉的评审者
3. **透明性**: 每个决策都可以追溯到具体的观点和权重
4. **可扩展性**: 可以独立处理多篇论文
5. **可复现性**: 所有中间结果都保存

## 未来改进方向

- 使用嵌入向量增强 RAG 以改善检索效果
- 支持更多主题
- 权重和分数的可视化
- 批量处理多篇论文
- 与评审平台集成
