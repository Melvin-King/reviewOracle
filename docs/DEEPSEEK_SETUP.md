# DeepSeek 配置指南

## 配置方式

DeepSeek 支持两种配置方式：

### 方式 1：在 config.yaml 中配置（推荐）

编辑 `config.yaml` 文件：

```yaml
llm:
  provider: "deepseek"
  api_key: "sk-your-deepseek-api-key-here"  # 直接填写你的 API key
  model: "deepseek-chat"  # 或 "deepseek-coder"
  temperature: 0.3
  max_tokens: 2000
```

### 方式 2：使用环境变量（更安全）

1. 设置环境变量：
   ```bash
   # Windows PowerShell
   $env:DEEPSEEK_API_KEY="sk-your-deepseek-api-key-here"
   
   # Windows CMD
   set DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
   
   # Linux/Mac
   export DEEPSEEK_API_KEY="sk-your-deepseek-api-key-here"
   ```

2. 在 `config.yaml` 中：
   ```yaml
   llm:
     provider: "deepseek"
     api_key: ""  # 留空，会从环境变量读取
     model: "deepseek-chat"
     temperature: 0.3
   ```

### 方式 3：使用 .env 文件（推荐用于开发）

1. 在项目根目录创建 `.env` 文件：
   ```
   DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
   ```

2. 安装 python-dotenv（已在 requirements.txt 中）：
   ```bash
   pip install python-dotenv
   ```

3. 在代码中加载（可选，如果使用环境变量方式会自动读取）

## 获取 DeepSeek API Key

1. 访问 [DeepSeek 官网](https://www.deepseek.com/)
2. 注册/登录账号
3. 进入 API 管理页面
4. 创建新的 API Key
5. 复制 API Key（格式类似：`sk-xxxxxxxxxxxxx`）

## 模型选择

- **deepseek-chat**: 通用对话模型，适合大多数任务
- **deepseek-coder**: 代码生成专用模型，适合代码相关任务

## 注意事项

1. **API Key 安全**：
   - 不要将 API Key 提交到 Git 仓库
   - `.env` 文件已在 `.gitignore` 中
   - 如果直接在 `config.yaml` 中填写，注意不要提交到 Git

2. **API 地址**：
   - DeepSeek 默认 API 地址：`https://api.deepseek.com`
   - 通常不需要手动设置 `base_url`
   - 如果需要自定义，可以在 config.yaml 中添加 `base_url` 字段

3. **费用**：
   - 注意 DeepSeek 的 API 调用费用
   - 建议设置使用限额

## 测试配置

运行以下命令测试配置是否正确：

```python
from src.utils.llm_client import LLMClient

# 测试 DeepSeek 连接
client = LLMClient(
    provider="deepseek",
    model="deepseek-chat",
    api_key="your-api-key"  # 或从环境变量读取
)

response = client.call("你好，请简单介绍一下自己")
print(response)
```

## 故障排查

1. **错误：未找到 API key**
   - 检查环境变量是否正确设置
   - 检查 config.yaml 中的 api_key 是否填写
   - 确认环境变量名称是 `DEEPSEEK_API_KEY`

2. **错误：API 调用失败**
   - 检查 API key 是否有效
   - 检查网络连接
   - 确认账户余额充足

3. **错误：模型不存在**
   - 确认模型名称正确：`deepseek-chat` 或 `deepseek-coder`
   - 检查 DeepSeek 是否更新了模型名称

