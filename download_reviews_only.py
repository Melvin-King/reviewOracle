"""单独下载 reviews 的脚本，可以等待更长时间"""
import sys
sys.path.insert(0, '.')
from src.data.downloader import NIPSDownloader
import time

# 论文信息
papers = [
    ('paper_21497', 'aVh9KRZdRk'),
    ('paper_19094', 'REIK4SZMJt'),
    ('paper_19076', 'gojL67CfS8')
]

downloader = NIPSDownloader()

print("=" * 60)
print("开始下载 Reviews")
print("=" * 60)

for paper_id, forum_id in papers:
    print(f"\n处理论文: {paper_id} (forum: {forum_id})")
    print("等待 60 秒以避免 429 错误...")
    time.sleep(60)
    
    reviews = downloader.download_reviews(paper_id, forum_id)
    print(f"获取到 {len(reviews)} 个 reviews")
    
    if reviews:
        for r in reviews:
            print(f"  - {r['reviewer_id']}: {len(r.get('content', ''))} 字符")

print("\n" + "=" * 60)
print("完成！")

