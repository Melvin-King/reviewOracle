# 实验运行快速参考

## 一、输入文件位置

| 数据类型 | 路径 | 示例 |
|---------|------|------|
| NIPS论文PDF | `data/raw/papers/{paper_id}.pdf` | `paper_19076.pdf` |
| NIPS评审JSON | `data/raw/reviews/{paper_id}_reviews.json` | `paper_19076_reviews.json` |
| ICLR Accepted PDF | `data/raw/iclr2024/papers/accepted/{paper_id}.pdf` | `eepoE7iLpL.pdf` |
| ICLR Rejected PDF | `data/raw/iclr2024/papers/rejected/{paper_id}.pdf` | `ApjY32f3Xr.pdf` |
| ICLR评审JSON | `data/raw/iclr2024/reviews/{paper_id}_reviews.json` | `eepoE7iLpL_reviews.json` |

---

## 二、运行脚本与输出文件

### Step 1: 观点提取

**脚本**：`run_step1_extraction.py`

**输入**：
- `data/raw/reviews/{paper_id}_reviews.json`

**输出**：
- `data/processed/extracted/{paper_id}_claims.json`

**运行**：
```bash
python run_step1_extraction.py
```

---

### Step 2: 事实验证

**脚本**：
- 单篇：`run_step2_verification.py`
- 批量：`run_step2_batch.py`

**输入**：
- `data/processed/extracted/{paper_id}_claims.json` (Step 1输出)
- `data/raw/papers/{paper_id}.pdf` (论文PDF)

**输出**：
- `data/results/verifications/{paper_id}_verified.json`

**运行**：
```bash
# 单篇（需修改脚本中的PAPER_ID）
python run_step2_verification.py

# 批量
python run_step2_batch.py
```

---

### Step 3: 权重计算

**脚本**：
- 单篇：`run_step3_weighting.py`
- 批量：`run_step3_batch.py`

**输入**：
- `data/processed/extracted/{paper_id}_claims.json` (Step 1输出)
- `data/results/verifications/{paper_id}_verified.json` (Step 2输出)

**输出**：
- `data/results/weights/{paper_id}_weights.json`

**运行**：
```bash
# 单篇（需修改脚本中的PAPER_ID）
python run_step3_weighting.py

# 批量
python run_step3_batch.py
```

---

### Step 4: 报告合成

**脚本**：
- 单篇：`run_step4_synthesis.py`
- 批量：`run_step4_batch.py`

**输入**：
- `data/processed/extracted/{paper_id}_claims.json` (Step 1输出)
- `data/results/verifications/{paper_id}_verified.json` (Step 2输出)
- `data/results/weights/{paper_id}_weights.json` (Step 3输出)

**输出**：
- `data/results/synthesis/{paper_id}_report.md`

**运行**：
```bash
# 单篇（需修改脚本中的PAPER_ID）
python run_step4_synthesis.py

# 批量
python run_step4_batch.py
```

---

## 三、完整流程运行

### 方法1：使用Pipeline API

```python
from src.pipeline import EVWPipeline

pipeline = EVWPipeline(config_path="config.yaml")

# 完整流程
pipeline.run_pipeline("paper_19076")

# 或分步运行
pipeline.step1_extraction("paper_19076")
pipeline.step2_verification("paper_19076")
pipeline.step3_weighting("paper_19076")
pipeline.step4_synthesis("paper_19076")
```

### 方法2：使用命令行脚本

```bash
# 完整流程
python scripts/run_pipeline.py --paper-id paper_19076

# 只运行Step 2
python scripts/run_pipeline.py --paper-id paper_19076 --step 2
```

### 方法3：ICLR 2024批量处理

```bash
# 运行Step 1, 2, 3（批量）
python run_iclr_pipeline_steps.py
```

---

## 四、结果分析脚本

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `calculate_prediction_accuracy.py` | 预测准确率 | 所有验证和权重结果 | `data/results/iclr2024_prediction_accuracy.json` |
| `analyze_iclr_results.py` | 详细统计 | `iclr2024_pipeline_results.json` | `data/results/iclr2024_statistics.json` |
| `generate_final_statistics.py` | 对比分析 | `iclr2024_pipeline_results.json` | `data/results/iclr2024_comparison_report.json` |
| `detailed_prediction_analysis.py` | 详细预测分析 | 所有验证和权重结果 | 控制台输出 |

---

## 五、文件流转图

```
输入
├── data/raw/papers/{paper_id}.pdf
└── data/raw/reviews/{paper_id}_reviews.json
    │
    ├─ Step 1 ─► data/processed/extracted/{paper_id}_claims.json
    │   │
    │   ├─ Step 2 ─► data/results/verifications/{paper_id}_verified.json
    │   │   │
    │   │   ├─ Step 3 ─► data/results/weights/{paper_id}_weights.json
    │   │   │   │
    │   │   │   └─ Step 4 ─► data/results/synthesis/{paper_id}_report.md
```

---

## 六、快速检查清单

- [ ] 输入文件已准备（PDF + reviews JSON）
- [ ] `config.yaml` 配置正确（LLM API key等）
- [ ] 已运行 Step 1（提取观点）
- [ ] 已运行 Step 2（事实验证）
- [ ] 已运行 Step 3（权重计算）
- [ ] 已运行 Step 4（报告合成）
- [ ] 检查输出文件是否生成

---

## 七、常见问题

**Q: 如何查看中间结果？**
```bash
# 查看提取的观点
cat data/processed/extracted/paper_19076_claims.json

# 查看验证结果
cat data/results/verifications/paper_19076_verified.json

# 查看权重
cat data/results/weights/paper_19076_weights.json
```

**Q: 如何重新运行某个步骤？**
```bash
# 删除对应输出文件，然后重新运行
rm data/results/verifications/paper_19076_verified.json
python run_step2_verification.py
```

**Q: 如何批量处理？**
修改脚本中的 `PAPERS` 或 `PAPER_ID` 列表，或使用批量处理脚本。


