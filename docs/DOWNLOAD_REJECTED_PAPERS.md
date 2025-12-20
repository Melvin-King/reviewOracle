# 下载被拒绝的论文

## 方法一：手动提供 Forum ID（推荐）

由于 OpenReview API 的限制，直接搜索被拒绝的论文比较困难。推荐使用手动方式：

### 步骤

1. **访问 OpenReview 会议页面**
   - 打开：https://openreview.net/group?id=NeurIPS.cc/2024/Conference

2. **筛选被拒绝的论文**
   - 在页面上使用筛选功能，选择 "Rejected" 状态
   - 或者浏览论文列表，查找状态为 "Rejected" 的论文

3. **获取 Forum ID**
   - 点击论文标题进入详情页
   - 从 URL 中提取 forum ID
   - 例如：`https://openreview.net/forum?id=XXXXX` 中的 `XXXXX` 就是 forum ID

4. **使用脚本下载**
   ```bash
   python download_rejected_papers_manual.py
   ```
   - 在脚本中填写 `rejected_forum_ids` 列表
   - 运行脚本即可下载 PDF 和 Reviews

## 方法二：通过低 Rating 推断（实验性）

可以通过搜索低 rating 的论文来推断被拒绝的论文：

```bash
python find_low_rating_papers.py
```

这个脚本会：
1. 搜索 NeurIPS 2024 的论文
2. 检查每篇论文的 reviewer ratings
3. 筛选出平均 rating < 5.0 的论文（可能是被拒绝的）
4. 下载这些论文的 PDF 和 Reviews

**注意**：这种方法只是推断，不是100%准确。有些低 rating 的论文可能最终被接受了（经过 rebuttal 后）。

## 方法三：使用已知的 Rejected 论文列表

如果你有已知的被拒绝论文列表（例如从其他来源获取），可以直接使用 `download_rejected_papers_manual.py` 脚本。

## 文件说明

- `download_rejected_papers.py`: 自动搜索被拒绝论文（可能因 API 限制失败）
- `download_rejected_papers_manual.py`: 手动提供 Forum ID 下载（推荐）
- `find_low_rating_papers.py`: 通过低 rating 推断被拒绝论文（实验性）

## 注意事项

1. **API 限制**：OpenReview API 有严格的速率限制，下载时请耐心等待
2. **状态验证**：下载前脚本会自动验证论文状态，确保是 "Rejected"
3. **Reviews 可用性**：不是所有被拒绝的论文都有公开的 reviews
4. **数据保存**：
   - PDF 保存在：`data/raw/papers/{forum_id}.pdf`
   - Reviews 保存在：`data/raw/reviews/{forum_id}_reviews.json`
   - 论文信息保存在：`data/raw/papers/{forum_id}_info.json`

