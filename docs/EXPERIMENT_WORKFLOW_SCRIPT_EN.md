# Experiment Workflow Presentation Script (English)
**Duration: ~6 minutes**

---

## Opening (30 seconds)

Good morning/afternoon everyone. Today I'll walk you through the E-V-W Pipeline experiment workflow. This system evaluates academic paper reviews through four sequential steps: extraction, verification, weighting, and synthesis. Each step produces structured outputs that can be inspected and the entire process is reproducible.

Let me start with input file preparation.

---

## Part I: Input File Preparation (1 minute)

You need three types of input files:

**First, paper PDFs**: 
- NIPS papers: `data/raw/papers/{paper_id}.pdf`
- ICLR 2024: `data/raw/iclr2024/papers/accepted/` or `rejected/`

**Second, review JSON files**:
- NIPS: `data/raw/reviews/{paper_id}_reviews.json`
- ICLR 2024: `data/raw/iclr2024/reviews/{paper_id}_reviews.json`

Each review file contains review text, ratings, and reviewer information.

**Third, configuration file**: `config.yaml` controls LLM settings, RAG methods, and thresholds.

Once these are ready, you can start the workflow.

---

## Part II: Four-Step Workflow (3 minutes)

### Step 1: Claim Extraction (45 seconds)

**Purpose**: Transform review text into structured atomic claims.

**Execution**: `python run_step1_extraction.py`

**What It Does**:
- Takes review JSON as input
- Uses LLM to extract atomic claims
- For each claim, extracts: ID, topic, sentiment, statement, and evidence type

**Output**: `data/processed/extracted/{paper_id}_claims.json`

**Time**: 2-5 seconds per paper

**Key Point**: This step doesn't read the paper - only analyzes reviews.

---

### Step 2: Fact Verification (45 seconds)

**Purpose**: Verify claims against paper content.

**Execution**: `python run_step2_verification.py` or `run_step2_batch.py`

**What It Does**:
- Takes claims from Step 1 and paper PDF
- Identifies relevant paper sections automatically
- Uses hybrid RAG (sparse + dense retrieval) with reranking
- Verifies each claim: True, False, or Partially_True

**Output**: `data/results/verifications/{paper_id}_verified.json`

**Time**: 30-60 seconds per paper

**Key Features**: Section filtering improves precision by 15-25%, reranking adds another 10-20%.

---

### Step 3: Weight Calculation (45 seconds)

**Purpose**: Calculate reviewer credibility weights.

**Execution**: `python run_step3_weighting.py` or `run_step3_batch.py`

**What It Does**:
- Takes claims and verification results
- Calculates two metrics per reviewer:
  - **Hollowness**: Proportion of claims without evidence
  - **Hallucination**: Proportion of false claims
- Computes weight: `Weight = 1.0 - (α × Hollowness + β × Hallucination)`

**Output**: `data/results/weights/{paper_id}_weights.json`

**Time**: <1 second per paper

**Key Point**: Completely objective - no LLM judgment, purely data-driven.

---

### Step 4: Report Synthesis (45 seconds)

**Purpose**: Generate final meta-review with weighted voting.

**Execution**: `python run_step4_synthesis.py` or `run_step4_batch.py`

**What It Does**:
- Filters out false claims
- Groups claims by topic
- Performs weighted voting (sentiment × reviewer weight)
- Converts to 10-point scale
- Makes final decision: ACCEPT if score ≥ 5.0, otherwise REJECT

**Output**: `data/results/synthesis/{paper_id}_report.md`

**Time**: 5-10 seconds per paper

---

## Part III: Execution Methods (1 minute)

You can run the workflow in three ways:

**Method 1: Pipeline API** (Recommended)
```python
from src.pipeline import EVWPipeline
pipeline = EVWPipeline(config_path="config.yaml")
pipeline.run_pipeline("paper_19076")
```

**Method 2: Command Line**
```bash
python scripts/run_pipeline.py --paper-id paper_19076
```

**Method 3: Individual Scripts**
Run each step's script separately for maximum control.

For ICLR 2024 batch processing:
```bash
python run_iclr_pipeline_steps.py  # Runs Step 1, 2, 3
```

---

## Part IV: Result Analysis (30 seconds)

After running the pipeline, use analysis scripts:

- `calculate_prediction_accuracy.py` - Compare predictions with ground truth
- `generate_final_statistics.py` - Compare accepted vs rejected papers
- `detailed_prediction_analysis.py` - Per-paper detailed analysis

All results are saved as JSON files in `data/results/` for further processing.

---

## Important Notes (30 seconds)

**Key Points**:
1. **Consistency**: Use the same `paper_id` across all steps
2. **Dependencies**: Steps must run in order (2 needs 1, 3 needs 1&2, 4 needs all)
3. **Caching**: Step 2 caches RAG indices - subsequent runs are faster
4. **Configuration**: Check `config.yaml` before running, especially API keys

---

## Conclusion (30 seconds)

To summarize, the E-V-W Pipeline workflow is:
- **Modular**: Each step is independent with inspectable outputs
- **Transparent**: All calculations are explicit and reproducible
- **Flexible**: Multiple execution methods
- **Comprehensive**: Includes analysis tools

The workflow transforms unstructured reviews into objective, evidence-based meta-reviews with quantified credibility and topic assessments.

Thank you. I'm happy to answer questions.

---

## Timing Breakdown

- **Opening**: 30 seconds
- **Part I: Input Preparation**: 1 minute
- **Part II: Four Steps**: 3 minutes (45 seconds each)
- **Part III: Execution Methods**: 1 minute
- **Part IV: Result Analysis**: 30 seconds
- **Important Notes**: 30 seconds
- **Conclusion**: 30 seconds
- **Total**: ~6 minutes

---

## Speaking Tips

1. **Pace**: Speak at 150-160 words per minute
2. **Pauses**: Brief pauses after each step explanation
3. **Emphasis**: Highlight file paths and key numbers (15-25%, 10-20%)
4. **Visual Aids**: Consider showing file structure or live demo
5. **Questions**: Encourage questions, especially after major sections

---

## Potential Q&A Topics

- How do I handle papers with non-standard sections?
- Can I run steps in parallel?
- How do I customize the weight formula?
- What if extraction finds no claims?
- How do I interpret the 10-point scores?
