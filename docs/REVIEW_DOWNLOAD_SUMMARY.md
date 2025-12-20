# Reviews 下载问题总结和解决方案

## 问题分析

经过测试发现：
1. ✅ **API 地址正确**：使用 `api2.openreview.net`（不是 `api.openreview.net`）
2. ✅ **查询参数正确**：使用 `domain` 和 `forum` 参数
3. ✅ **数据结构正确**：`invitations` 是数组，包含 `Official_Review`
4. ❌ **频率限制严格**：API 返回 429 错误，即使等待 2-5 分钟仍然失败

## 已找到的 Reviews

从测试中发现，论文 `aVh9KRZdRk` 有 **4 个 Official Review**：
- Review 1: `m1s5JPqAc9` (Reviewer CrUb, Rating: 7)
- Review 2: `RPlLeNuaca` (Reviewer Jerg, Rating: 7)  
- Review 3: `ZLQwBMiHgE` (Reviewer PjEW, Rating: 8)
- Review 4: `PdJabwbJeE` (Reviewer rwBm, Rating: 7)

## 解决方案

### 方案 1：手动从网页复制（最快）

1. 访问论文页面：https://openreview.net/forum?id=aVh9KRZdRk
2. 找到 4 个 Official Review
3. 复制每个 review 的内容到对应的 JSON 文件

### 方案 2：等待更长时间后重试

API 频率限制可能需要等待 **10-15 分钟** 才能重置。可以：
1. 运行 `python download_reviews_smart.py`（每次间隔 3 分钟）
2. 或者手动等待 15 分钟后运行单篇下载

### 方案 3：使用网页抓取（需要 Selenium）

实现基于 Selenium 的网页抓取，直接从 HTML 中提取 reviews。

### 方案 4：使用已知的 Review ID

如果知道 review 的 ID，可以直接通过 ID 获取：
```python
# 直接通过 ID 获取 review
response = requests.get('https://api2.openreview.net/notes/m1s5JPqAc9')
```

## 当前代码状态

代码已经修复：
- ✅ 使用正确的 API 地址
- ✅ 正确解析 `invitations` 数组
- ✅ 正确提取 review 内容（summary, strengths, weaknesses 等）
- ✅ 增加了重试机制和长延迟

## 建议

由于 API 频率限制非常严格，建议：
1. **先手动复制一篇论文的 reviews** 测试系统
2. **或者等待更长时间**（比如 15-30 分钟）后再尝试 API
3. **或者实现网页抓取**作为备选方案

