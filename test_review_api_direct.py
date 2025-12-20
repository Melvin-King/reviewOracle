"""直接测试 reviews API，使用更长的等待时间"""
import requests
import time
import json

forum_id = 'aVh9KRZdRk'
url = 'https://api2.openreview.net/notes'

# 使用网页实际调用的参数
params = {
    "count": "true",
    "domain": "NeurIPS.cc/2024/Conference",
    "forum": forum_id,
    "details": "writable,signatures,invitation,presentation,tags",
    "trash": "true",
    "limit": 1000
}

print("=" * 60)
print("测试 Reviews API")
print("=" * 60)
print(f"\nForum ID: {forum_id}")
print("等待 120 秒（2分钟）以避免 429 错误...")
print("（如果还是失败，可能需要等待更长时间或使用其他方法）\n")

time.sleep(120)

print("发送请求...")
try:
    response = requests.get(url, params=params, timeout=60, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        all_notes = data.get('notes', [])
        print(f"\n获取到 {len(all_notes)} 个 notes")
        
        # 过滤出 reviews
        reviews = []
        for note in all_notes:
            invitation = note.get('invitation', '')
            if 'Official_Review' in invitation:
                reviews.append(note)
        
        print(f"其中 {len(reviews)} 个是 Official Review")
        
        if reviews:
            print("\nReviews 详情:")
            for i, review in enumerate(reviews, 1):
                content = review.get('content', {})
                print(f"\nReview {i}:")
                print(f"  ID: {review.get('id')}")
                print(f"  Invitation: {review.get('invitation', 'N/A')}")
                if 'summary' in content:
                    summary = content['summary'].get('value', '')
                    print(f"  Summary: {summary[:100]}..." if summary else "  Summary: N/A")
                if 'rating' in content:
                    print(f"  Rating: {content['rating'].get('value', 'N/A')}")
        else:
            print("\n未找到 Official Review")
            print("所有 notes 的 invitation:")
            for note in all_notes[:10]:
                print(f"  - {note.get('invitation', 'N/A')}")
    else:
        print(f"错误: {response.text[:500]}")
        
except Exception as e:
    print(f"异常: {e}")

print("\n" + "=" * 60)

