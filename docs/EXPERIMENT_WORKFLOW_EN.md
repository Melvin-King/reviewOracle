# Experiment Workflow and File Documentation

## Complete Experiment Workflow Overview

```
Input Data Preparation
    ↓
Step 1: Claim Extraction (Extraction)
    ↓
Step 2: Fact Verification (Verification)
    ↓
Step 3: Weight Calculation (Weighting)
    ↓
Step 4: Report Synthesis (Synthesis)
    ↓
Result Analysis and Statistics
```

---

## I. Input File Preparation

### 1.1 Paper PDF Files

**Locations**:
- NIPS Papers: `data/raw/papers/{paper_id}.pdf`
- ICLR 2024 Accepted: `data/raw/iclr2024/papers/accepted/{paper_id}.pdf`
- ICLR 2024 Rejected: `data/raw/iclr2024/papers/rejected/{paper_id}.pdf`

**Examples**:
```
data/raw/papers/paper_19076.pdf
data/raw/iclr2024/papers/accepted/eepoE7iLpL.pdf
data/raw/iclr2024/papers/rejected/ApjY32f3Xr.pdf
```

### 1.2 Review JSON Files

**Locations**:
- NIPS Reviews: `data/raw/reviews/{paper_id}_reviews.json`
- ICLR 2024 Reviews: `data/raw/iclr2024/reviews/{paper_id}_reviews.json`

**Format**:
```json
[
  {
    "id": "review_id",
    "content": {
      "review": "Review text content...",
      "rating": "8"
    },
    "signatures": ["~Reviewer1"]
  }
]
```

**Examples**:
```
data/raw/reviews/paper_19076_reviews.json
data/raw/iclr2024/reviews/eepoE7iLpL_reviews.json
```

### 1.3 Configuration File

**Location**: `config.yaml`

**Main Contents**:
- LLM configuration (provider, model, temperature)
- RAG configuration (method, use_reranking, embedding_model, etc.)
- Weight calculation configuration (alpha, beta)
- Synthesis configuration (accept_threshold, topics, etc.)

---

## II. Experiment Steps and Execution Files

### Step 1: Claim Extraction (Extraction)

**Execution Scripts**:
```bash
# Single paper
python run_step1_extraction.py

# Batch processing (need to modify paper_ids list in script)
python run_step1_extraction.py
```

**Input Files**:
- `data/raw/reviews/{paper_id}_reviews.json` - Review JSON file

**Output Files**:
- `data/processed/extracted/{paper_id}_claims.json` - Structured claims

**Output Format**:
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

**Processing Time**: ~2-5 seconds/paper

---

### Step 2: Fact Verification (Verification)

**Execution Scripts**:
```bash
# Single paper
python run_step2_verification.py

# Batch processing
python run_step2_batch.py

# ICLR 2024 batch processing
python run_iclr_pipeline_steps.py  # Includes Step 1, 2, 3
```

**Input Files**:
- `data/processed/extracted/{paper_id}_claims.json` - Step 1 output
- `data/raw/papers/{paper_id}.pdf` - Paper PDF (or parsed text cache)

**Output Files**:
- `data/results/verifications/{paper_id}_verified.json` - Verification results
- `data/processed/rag_indices/{paper_id}.*` - RAG index cache (optional)

**Output Format**:
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

**Processing Time**: ~30-60 seconds/paper (depends on number of claims)

**Key Features**:
- Automatic section identification and filtering
- Supports sparse retrieval, dense retrieval, hybrid retrieval
- Supports reranking optimization

---

### Step 3: Weight Calculation (Weighting)

**Execution Scripts**:
```bash
# Single paper
python run_step3_weighting.py

# Batch processing
python run_step3_batch.py

# ICLR 2024 batch processing
python run_iclr_pipeline_steps.py  # Includes Step 1, 2, 3
```

**Input Files**:
- `data/processed/extracted/{paper_id}_claims.json` - Step 1 output
- `data/results/verifications/{paper_id}_verified.json` - Step 2 output

**Output Files**:
- `data/results/weights/{paper_id}_weights.json` - Reviewer weights

**Output Format**:
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

**Processing Time**: <1 second/paper

---

### Step 4: Report Synthesis (Synthesis)

**Execution Scripts**:
```bash
# Single paper
python run_step4_synthesis.py

# Batch processing
python run_step4_batch.py
```

**Input Files**:
- `data/processed/extracted/{paper_id}_claims.json` - Step 1 output
- `data/results/verifications/{paper_id}_verified.json` - Step 2 output
- `data/results/weights/{paper_id}_weights.json` - Step 3 output

**Output Files**:
- `data/results/synthesis/{paper_id}_report.md` - Meta-Review report

**Output Format**: Markdown format, including:
- Reviewer credibility weights
- Topic scores (10-point scale)
- Weighted voting results
- Final decision (ACCEPT/REJECT)

**Processing Time**: ~5-10 seconds/paper

---

## III. Complete Workflow Execution

### 3.1 Using Pipeline Class (Recommended)

**Script**: `scripts/run_pipeline.py` or use Python directly

```python
from src.pipeline import EVWPipeline

# Initialize
pipeline = EVWPipeline(config_path="config.yaml")

# Run complete workflow
pipeline.run_pipeline("paper_19076")

# Or run step by step
claims = pipeline.step1_extraction("paper_19076")
verifications = pipeline.step2_verification("paper_19076")
weights = pipeline.step3_weighting("paper_19076")
report = pipeline.step4_synthesis("paper_19076")
```

### 3.2 Using Command Line Script

```bash
# Run complete workflow
python scripts/run_pipeline.py --paper-id paper_19076

# Run only specific step
python scripts/run_pipeline.py --paper-id paper_19076 --step 2
```

### 3.3 ICLR 2024 Batch Processing

```bash
# Run Step 1, 2, 3 (batch)
python run_iclr_pipeline_steps.py
```

---

## IV. Result Analysis and Statistics

### 4.1 Prediction Accuracy Analysis

**Script**: `calculate_prediction_accuracy.py`

**Input**:
- `data/results/verifications/{paper_id}_verified.json` - Verification results for all papers
- `data/results/weights/{paper_id}_weights.json` - Weight results for all papers
- Paper PDF locations (to determine ground truth: accepted/rejected)

**Output**:
- `data/results/iclr2024_prediction_accuracy.json` - Prediction accuracy results

**Execution**:
```bash
python calculate_prediction_accuracy.py
```

### 4.2 Detailed Statistical Analysis

**Script**: `analyze_iclr_results.py`

**Input**:
- `data/results/iclr2024_pipeline_results.json` - Pipeline results summary

**Output**:
- `data/results/iclr2024_statistics.json` - Detailed statistics

**Execution**:
```bash
python analyze_iclr_results.py
```

### 4.3 Comparative Analysis Report

**Script**: `generate_final_statistics.py`

**Input**:
- `data/results/iclr2024_pipeline_results.json`

**Output**:
- `data/results/iclr2024_comparison_report.json` - Accepted vs Rejected comparison report

**Execution**:
```bash
python generate_final_statistics.py
```

### 4.4 Detailed Prediction Analysis

**Script**: `detailed_prediction_analysis.py`

**Input**:
- Verification and weight results for all papers

**Output**:
- Console output: Detailed scores and prediction results for each paper

**Execution**:
```bash
python detailed_prediction_analysis.py
```

---

## V. Complete File Structure

```
data/
├── raw/                          # Raw input data
│   ├── papers/                   # NIPS paper PDFs
│   │   └── {paper_id}.pdf
│   ├── reviews/                  # NIPS review JSONs
│   │   └── {paper_id}_reviews.json
│   └── iclr2024/                 # ICLR 2024 data
│       ├── papers/
│       │   ├── accepted/
│       │   │   └── {paper_id}.pdf
│       │   └── rejected/
│       │       └── {paper_id}.pdf
│       └── reviews/
│           └── {paper_id}_reviews.json
│
├── processed/                    # Intermediate processing results
│   ├── extracted/                # Step 1 output
│   │   └── {paper_id}_claims.json
│   ├── papers/                   # Parsed paper text (cache)
│   │   └── {paper_id}.txt
│   └── rag_indices/              # RAG index cache (optional)
│       └── {paper_id}.*
│
└── results/                      # Final results
    ├── verifications/            # Step 2 output
    │   └── {paper_id}_verified.json
    ├── weights/                   # Step 3 output
    │   └── {paper_id}_weights.json
    ├── synthesis/                 # Step 4 output
    │   └── {paper_id}_report.md
    └── iclr2024_*.json           # Statistical analysis results
```

---

## VI. Quick Start Examples

### Example 1: Processing Single NIPS Paper

```bash
# 1. Ensure input files exist
# data/raw/papers/paper_19076.pdf
# data/raw/reviews/paper_19076_reviews.json

# 2. Run complete workflow
python run_step1_extraction.py      # Modify PAPER_ID in script
python run_step2_verification.py    # Modify PAPER_ID in script
python run_step3_weighting.py      # Modify PAPER_ID in script
python run_step4_synthesis.py      # Modify PAPER_ID in script

# 3. View results
# data/results/synthesis/paper_19076_report.md
```

### Example 2: Batch Processing ICLR 2024 Papers

```bash
# 1. Ensure papers and reviews are downloaded
# data/raw/iclr2024/papers/accepted/*.pdf
# data/raw/iclr2024/papers/rejected/*.pdf
# data/raw/iclr2024/reviews/*_reviews.json

# 2. Run Step 1, 2, 3
python run_iclr_pipeline_steps.py

# 3. Run Step 4 (if needed)
python run_step4_batch.py  # Need to modify paper_ids in script

# 4. Statistical analysis
python calculate_prediction_accuracy.py
python generate_final_statistics.py
```

### Example 3: Using Pipeline API

```python
from src.pipeline import EVWPipeline

pipeline = EVWPipeline(config_path="config.yaml")

# Single paper complete workflow
paper_id = "paper_19076"
pipeline.run_pipeline(paper_id)

# Or execute step by step
claims = pipeline.step1_extraction(paper_id)
verifications = pipeline.step2_verification(paper_id)
weights = pipeline.step3_weighting(paper_id)
report = pipeline.step4_synthesis(paper_id)
```

---

## VII. Important Notes

1. **File Naming**: Ensure paper_id is consistent across all steps
2. **Dependency Order**: Step 2 depends on Step 1, Step 3 depends on Step 1 and 2, Step 4 depends on Step 1, 2, 3
3. **Caching Mechanism**: Step 2 caches RAG indices, repeated runs will be faster
4. **Configuration Check**: Check LLM API key and model configuration in `config.yaml` before running
5. **Error Handling**: In batch processing, failure of a single paper will not interrupt the entire workflow

---

## VIII. Frequently Asked Questions

**Q: How to view intermediate results?**
A: All intermediate results are saved in `data/processed/` and `data/results/` directories, you can directly view the JSON files.

**Q: How to rerun a specific step?**
A: Delete the corresponding output file, then rerun the script for that step.

**Q: How to batch process multiple papers?**
A: Modify the paper_ids list in the script, or use batch processing scripts (e.g., `run_step2_batch.py`).

**Q: Where are RAG indices?**
A: By default saved in `data/processed/rag_indices/`, can be deleted to force rebuild.

**Q: How to change configuration?**
A: Modify the `config.yaml` file, then reinitialize the Pipeline.


