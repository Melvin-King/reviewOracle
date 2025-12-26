# E-V-W Evaluation Stack

提取-验证-加权栈系统，用于自动化分析学术论文评审。

## 项目结构

详细的项目结构说明请参考 [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml`，设置你的 API 密钥：

**使用 DeepSeek（推荐）**：
```yaml
llm:
  provider: "deepseek"
  api_key: "sk-your-deepseek-api-key-here"  # 或留空使用环境变量
  model: "deepseek-chat"  # 或 "deepseek-coder"
  temperature: 0.3
```

**使用 OpenAI**：
```yaml
llm:
  provider: "openai"
  api_key: "your-api-key-here"
  model: "gpt-4"
```

**使用环境变量（更安全）**：
```bash
# DeepSeek
export DEEPSEEK_API_KEY="sk-your-api-key-here"

# 或 OpenAI
export OPENAI_API_KEY="your-api-key-here"
```

详细配置说明请参考 [DEEPSEEK_SETUP.md](docs/DEEPSEEK_SETUP.md)

### 3. 下载数据

从 NIPS 2024 下载论文和 review：

```bash
python scripts/download_data.py --num-papers 3 --year 2024
```

### 4. 运行流程

处理单篇论文：

```bash
python scripts/run_pipeline.py --paper-id paper_001
```

或者只运行特定步骤：

```bash
python scripts/run_pipeline.py --paper-id paper_001 --step 1
```

## 系统架构

系统分为四个步骤：

1. **Extraction (结构化拆解)**：从 Review 中提取原子观点，分类证据类型
2. **Verification (事实落地)**：验证观点是否与论文一致
3. **Weighting (偏差计算)**：计算 Reviewer 的可信度权重
4. **Synthesis (合成决策)**：生成最终的 Meta-Review 报告

详细设计请参考：
- [Pipeline 总览与技术亮点](docs/PIPELINE_OVERVIEW.md) ⭐ **推荐阅读**
- [系统架构设计](docs/read.md)

## 开发状态

- [x] 项目结构设计
- [x] 基础框架搭建
- [ ] 数据下载模块（需要实现 OpenReview API 集成）
- [ ] Step 1: 结构化提取 Agent
- [ ] Step 2: 事实验证 Agent
- [ ] Step 3: 权重计算 Agent
- [ ] Step 4: 合成决策 Agent

## 注意事项

1. **数据下载**：当前 `downloader.py` 中的 OpenReview API 调用需要根据实际 API 文档实现
2. **API 密钥**：确保正确配置 LLM API 密钥
3. **数据格式**：Review 数据格式需要根据实际数据源调整

## 许可证

MIT License

