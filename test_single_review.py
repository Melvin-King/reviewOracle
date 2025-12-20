"""测试下载单篇论文的 reviews"""
import sys
sys.path.insert(0, '.')
from src.data.downloader import NIPSDownloader
import time

downloader = NIPSDownloader()

# 测试第一篇论文
paper_id = 'paper_21497'
forum_id = 'aVh9KRZdRk'

print("=" * 60)
print(f"测试下载论文 {paper_id} 的 Reviews")
print(f"Forum ID: {forum_id}")
print("=" * 60)

print("\n等待 60 秒以避免 429 错误...")
time.sleep(60)

print("\n开始下载...")
reviews = downloader.download_reviews(paper_id, forum_id)

print(f"\n结果: 获取到 {len(reviews)} 个 reviews")

if reviews:
    print("\nReviews 详情:")
    for i, r in enumerate(reviews, 1):
        print(f"\nReview {i} ({r['reviewer_id']}):")
        print(f"  - Review ID: {r['review_id']}")
        print(f"  - 内容长度: {len(r.get('content', ''))} 字符")
        if r.get('content'):
            print(f"  - 内容预览: {r['content'][:200]}...")
        if r.get('rating'):
            print(f"  - 评分: {r['rating']}")
        if r.get('confidence'):
            print(f"  - 置信度: {r['confidence']}")
else:
    print("\n未获取到 reviews，可能的原因：")
    print("  1. API 频率限制仍然生效")
    print("  2. 该论文可能没有公开的 reviews")
    print("  3. 需要更长的等待时间")

print("\n" + "=" * 60)

