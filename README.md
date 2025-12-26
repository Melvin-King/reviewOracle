# ReviewOracle

Extraction-verification-weighted stack system for automated analysis of academic paper reviews.

## Project Structure

Please refer to the detailed project structure description: [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. configuration

Edit `config.yaml` and set your API key:

**Using DeepSeek**：
```yaml
llm:
  provider: "deepseek"
  api_key: "sk-your-deepseek-api-key-here"  # Or leave it blank and use environment variables
  model: "deepseek-chat"  # or "deepseek-coder"
  temperature: 0.3
```

**Using OpenAI**：
```yaml
llm:
  provider: "openai"
  api_key: "your-api-key-here"
  model: "gpt-4"
```

**Use environment variables (safer)**：
```bash
# DeepSeek
export DEEPSEEK_API_KEY="sk-your-api-key-here"

# 或 OpenAI
export OPENAI_API_KEY="your-api-key-here"
```

Please refer to the detailed configuration instructions: [DEEPSEEK_SETUP.md](docs/DEEPSEEK_SETUP.md)

### 3. Download data

Download papers and reviews from NeurIPS 2024:

```bash
python scripts/download_data.py --num-papers 3 --year 2024
```

### 4. Operation process

Processing single papers:

```bash
python scripts/run_pipeline.py --paper-id paper_001
```

Or, run only specific steps:

```bash
python scripts/run_pipeline.py --paper-id paper_001 --step 1
```

## Precautions

1. **Data download**：The OpenReview API calls in the current `downloader.py` need to be implemented according to the actual API documentation.
2. **API key**：Ensure the LLM API key is configured correctly.
3. **Data format**：The data format needs to be adjusted according to the actual data source.

