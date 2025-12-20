import sys
sys.path.insert(0, '.')
from src.data.downloader import NIPSDownloader
import time

d = NIPSDownloader()
print('等待 20 秒避免 429...')
time.sleep(20)

# 测试下载第一个论文的 reviews
reviews = d.download_reviews('paper_21497', 'aVh9KRZdRk')
print(f'获取到 {len(reviews)} 个 reviews')
for r in reviews[:3]:
    print(f"  - {r['reviewer_id']}: {len(r.get('content', ''))} 字符")
    if r.get('content'):
        print(f"    内容预览: {r['content'][:100]}...")

