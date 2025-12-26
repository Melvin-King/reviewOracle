---
title: 無標題

---



### 框架名称：E-V-W Evaluation Stack (提取-验证-加权栈)

我们将处理流程严格切割为三个独立的数学化步骤：
1.  **Extraction (结构化拆解)**：把Review拆成原子观点，并**分类**证据类型
2.  **Verification (事实落地)**：只做True/False的二值判断（解决不一致问题）。
3.  **Weighting (偏差计算)**：基于前两步的结果计算可信度权重（解决偏差问题）。

---

### 详细架构设计

#### Step 1: Structure Extraction Agent (结构化提取层)
**任务**：这一步**不读Paper**，只读Review。它的核心任务是将Review文本转化为一张标准的“观点表”，并对**证据的质量**进行打标。

*   **输入**：Review Text
*   **核心逻辑**：将每句话拆解为 `Atom_Claim`，重点是提取 `Substantiation_Type`（支撑类型）。
*   **结构化输出 (JSON)**：
    ```json
    [
      {
        "id": "R1-C1",
        "topic": "Novelty",
        "sentiment": "Negative",
        "statement": "The proposed attention mechanism is not novel.",
        "substantiation_type": "Specific_Citation", // 关键字段：Specific_Citation / Vague / None
        "substantiation_content": "Similar to Vaswani et al. 2017"
      },
      {
        "id": "R1-C2",
        "topic": "Experiments",
        "sentiment": "Negative",
        "statement": "Experiments are weak.",
        "substantiation_type": "None", // 没有任何证据支撑的空对空指责
        "substantiation_content": null
      }
    ]
    ```
*   **结构化改进点**：在这里就把“有没有证据”结构化了。`None` 类型直接意味着潜在的“主观偏差”。

#### Step 2: Fact Verification Agent (事实验证层)
**任务**：这一步**引入Paper**。只针对 Step 1 中 `substantiation_type != None` 的观点进行验证。

*   **输入**：`Atom_Claim` + Paper PDF
*   **核心逻辑**：RAG（检索增强生成）。
*   **结构化输出 (JSON)**：
    ```json
    {
      "id": "R1-C1",
      "verification_result": "False", // 验证结果：True / False / Partially_True
      "verification_reason": "Paper explicitly mentions differences from Vaswani in Eq 3.",
      "confidence": 0.95
    }
    ```
*   **结构化改进点**：这一步完全客观，不涉及对Reviewer的评价，只看“他说的事实对不对”。

#### Step 3: Bias Calculation & Weighting (偏差计算与加权层)
**任务**：我们在这一步通过公式计算Reviewer的**信誉分 (Credibility Score)**，而不是靠LLM“感觉”。

*   **输入**：Step 1 的证据类型 + Step 2 的验证结果。
*   **逻辑算法**：
    我们定义一个Reviewer $R$ 的**偏差指数 (Bias Index)** 由两部分组成：
    1.  **空洞指数 (Hollowness)**：即 `substantiation_type == None` 的占比。如果一个Review全在骂但没证据，Hollowness极高。
    2.  **幻觉指数 (Hallucination)**：即 `verification_result == False` 的占比。如果给出的证据都被Paper反驳了，Hallucination极高。

    **权重计算公式**：
    $$ Weight(R) = 1.0 - (\alpha \times \text{Hollowness} + \beta \times \text{Hallucination}) $$
    *(其中 $\alpha, \beta$ 是惩罚系数)*

*   **输出**：每个Reviewer的最终权重 `{R1: 0.3, R2: 0.9, R3: 0.8}`。
    *   *R1被打低分的原因清晰可见：要么是空话多，要么是瞎编多。*

#### Step 4: Meta-Review Synthesis (合成决策层)
**任务**：基于加权后的观点生成最终报告。

*   **逻辑**：
    *   对于每一个 Topic (如 Novelty)：
        *   收集所有 Reviewer 的观点。
        *   过滤掉 `verification_result == False` 的观点（错误事实）。
        *   对剩余观点进行**加权投票**。
        *   $$ Score(Topic) = \sum (Reviewer\_Sentiment \times Weight(R)) $$
    *   **决策**：如果加权分 > 阈值，则 Accept。

---

