"""智能下载 reviews - 等待足够长时间避免 429"""
import sys
sys.path.insert(0, '.')
from src.data.downloader import NIPSDownloader
import time
from datetime import datetime

# 论文信息
papers = [
    ('paper_21497', 'aVh9KRZdRk', 'Learning to grok'),
    ('paper_19094', 'REIK4SZMJt', 'Trading Place for Space'),
    ('paper_19076', 'gojL67CfS8', 'Visual Autoregressive Modeling'),
]

downloader = NIPSDownloader()

print("=" * 70)
print("智能下载 Reviews")
print("=" * 70)
print("\n策略：每次请求间隔 3 分钟，避免 429 错误")
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

for i, (paper_id, forum_id, title) in enumerate(papers, 1):
    print(f"\n{'='*70}")
    print(f"论文 {i}/{len(papers)}: {paper_id}")
    print(f"标题: {title}")
    print(f"Forum ID: {forum_id}")
    print(f"{'='*70}")
    
    if i > 1:
        wait_seconds = 180  # 3 分钟
        print(f"\n等待 {wait_seconds} 秒（3分钟）以避免 API 频率限制...")
        print(f"开始等待: {datetime.now().strftime('%H:%M:%S')}")
        for remaining in range(wait_seconds, 0, -30):
            print(f"  剩余 {remaining} 秒...", end='\r')
            time.sleep(min(30, remaining))
        print(f"\n等待完成: {datetime.now().strftime('%H:%M:%S')}\n")
    
    print(f"开始下载 reviews...")
    reviews = downloader.download_reviews(paper_id, forum_id)
    
    print(f"\n结果: 获取到 {len(reviews)} 个 reviews")
    
    if reviews:
        print("\nReviews 详情:")
        for r in reviews:
            content_len = len(r.get('content', ''))
            print(f"  - {r['reviewer_id']}: {content_len} 字符, Rating: {r.get('rating', 'N/A')}")
            if r.get('content'):
                print(f"    预览: {r['content'][:150]}...")
    else:
        print("  [WARNING] 未获取到 reviews")
    
    print()

print("=" * 70)
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

