# DeepSeek Configuration Guide

## Configuration Methods

DeepSeek supports two configuration methods:

### Method 1: Configure in config.yaml (Recommended)

Edit the `config.yaml` file:

```yaml
llm:

provider: "deepseek"

api_key: "sk-your-deepseek-api-key-here" # Directly enter your API key

model: "deepseek-chat" # or "deepseek-coder"

temperature: 0.3

max_tokens: 2000

```

### Method 2: Use Environment Variables (More Secure)

1. Set environment variables:

```bash

# Windows PowerShell

$env:DEEPSEEK_API_KEY="sk-your-deepseek-api-key-here"

# Windows CMD

set DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here

# Linux/Mac

export DEEPSEEK_API_KEY="sk-your-deepseek-api-key-here"

```

2. In `config.yaml`:

``yaml

llm:

provider: "deepseek"

api_key: "" # Leave blank, will be read from environment variables

model: "deepseek-chat"

temperature: 0.3

```

### Method 3: Using .env files (recommended for development)

1. Create a `.env` file in the project root directory:

```
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here

```

2. Install python-dotenv (already in requirements.txt):

``bash

pip install python-dotenv

```

3. Load in code (optional, will be automatically read if using environment variables)

## Obtain DeepSeek API Key

1. Visit [DeepSeek Official Website](https://www.deepseek.com/)

2. Register/Log in to an account

3. Go to the API management page

4. Create a new API Key

5. Copy the API Key (format similar to: `sk-xxxxxxxxxxxxx`)

## Model Selection

- **deepseek-chat**: General dialogue model, suitable for most tasks

- **deepseek-coder**: Code generation model, suitable for code-related tasks

## Precautions

1. **API Key Security**:

- Do not commit the API Key to the Git repository

- The `.env` file is already in `.gitignore`

- If you fill it directly in `config.yaml`, be careful not to commit it to Git

2. **API Address**:

- DeepSeek default API Address: `https://api.deepseek.com`

- Usually, you don't need to manually set `base_url`.

- If you need to customize it, you can add the `base_url` field to `config.yaml`.

3. **Costs**:

- Note the API call costs of DeepSeek.

- It is recommended to set usage limits.

## Test Configuration

Run the following command to test if the configuration is correct:

``python
from src.utils.llm_client import LLMClient

# Test DeepSeek connection
client = LLMClient(
provider="deepseek",
model="deepseek-chat",

api_key="your-api-key" # or read from environment variables


response = client.call("Hello, please briefly introduce yourself")

print(response)

```

## Troubleshooting

1. **Error: API key not found**

- Check if the environment variables are set correctly.

- Check the `api_key` in `config.yaml`. 1. **Error: API call failed**

- Check if the API key is valid

- Check network connection

- Check account balance

3. **Error: Model does not exist**

- Check model name is correct: `deepseek-chat` or `deepseek-coder`

- Check if DeepSeek has updated the model name
