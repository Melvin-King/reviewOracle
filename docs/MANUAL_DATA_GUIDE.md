# 手动准备数据指南

由于 NeurIPS 2024 的论文可能还没有在 OpenReview 上完全公开，或者 API 访问有限制，你可以手动准备数据。

## 步骤 1: 准备论文 PDF

1. 从 NeurIPS 2024 官网或其他来源下载 3 篇论文的 PDF
2. 将 PDF 文件重命名为 `paper_001.pdf`, `paper_002.pdf`, `paper_003.pdf`
3. 放到 `data/raw/papers/` 目录下

## 步骤 2: 准备 Review 数据

已经为你创建了 review 模板文件：
- `data/raw/reviews/paper_001_reviews.json`
- `data/raw/reviews/paper_002_reviews.json`
- `data/raw/reviews/paper_003_reviews.json`

### Review 数据格式

每个 review JSON 文件包含一个数组，每个元素是一个 review 对象：

```json
[
  {
    "reviewer_id": "R1",
    "review_id": "paper_001_review_1",
    "content": "这里是完整的 review 内容...",
    "summary": "review 摘要（可选）",
    "strengths": "优点（可选）",
    "weaknesses": "缺点（可选）",
    "rating": "评分（可选）",
    "confidence": "置信度（可选）"
  },
  {
    "reviewer_id": "R2",
    ...
  }
]
```

### 如何获取 Review 内容

1. **从 OpenReview 网站手动复制**：
   - 访问 https://openreview.net
   - 搜索 NeurIPS 2024 的论文
   - 找到对应的 reviews
   - 复制 review 内容到 JSON 文件中

2. **从论文作者获取**：
   - 有些作者会在个人主页或 arXiv 上分享 reviews
   - 可以联系作者询问

3. **使用示例数据**：
   - 如果只是测试系统，可以使用示例 review 内容
   - 确保 `content` 字段包含完整的 review 文本

## 步骤 3: 验证数据

运行以下命令验证数据是否准备正确：

```python
from src.data.data_loader import DataLoader

loader = DataLoader()

# 检查论文
for paper_id in ['paper_001', 'paper_002', 'paper_003']:
    try:
        text = loader.load_paper_text(paper_id)
        print(f"✓ {paper_id}: PDF 解析成功 ({len(text)} 字符)")
    except Exception as e:
        print(f"✗ {paper_id}: {e}")
    
    # 检查 reviews
    reviews = loader.load_reviews(paper_id)
    print(f"  - Reviews: {len(reviews)} 个")
```

## 快速开始（使用模板）

如果只是想快速测试系统，可以使用模板数据：

```bash
# 创建模板
python -c "from src.data.downloader_manual import ManualDataPreparer; ManualDataPreparer().prepare_manual_data(['paper_001', 'paper_002', 'paper_003'])"

# 然后手动编辑 JSON 文件，填入实际的 review 内容
```

## 注意事项

1. **PDF 文件**：确保 PDF 文件可以正常解析（不是扫描版或加密的）
2. **Review 格式**：`content` 字段是必需的，其他字段可选
3. **编码**：确保 JSON 文件使用 UTF-8 编码
4. **数据质量**：review 内容应该尽可能完整，以便后续的提取和分析

## 下一步

数据准备完成后，可以运行：

```bash
python scripts/run_pipeline.py --paper-id paper_001
```

