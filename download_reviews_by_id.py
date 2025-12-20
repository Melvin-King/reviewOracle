"""直接通过 review ID 下载 reviews"""
import sys
sys.path.insert(0, '.')
import requests
import json
import time
from pathlib import Path

# 从之前的测试中已知的 review IDs
paper_reviews = {
    'paper_21497': {
        'forum_id': 'aVh9KRZdRk',
        'review_ids': ['m1s5JPqAc9', 'RPlLeNuaca', 'ZLQwBMiHgE', 'PdJabwbJeE']
    }
}

base_url = "https://api2.openreview.net"
reviews_dir = Path("data/raw/reviews")
reviews_dir.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("通过 Review ID 直接下载")
print("=" * 60)

for paper_id, info in paper_reviews.items():
    print(f"\n处理论文: {paper_id}")
    reviews = []
    
    for i, review_id in enumerate(info['review_ids'], 1):
        print(f"\n下载 Review {i}/{len(info['review_ids'])}: {review_id}")
        time.sleep(5)  # 每个请求间隔 5 秒
        
        try:
            url = f"{base_url}/notes/{review_id}"
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                note = response.json()
                content = note.get('content', {})
                
                # 构建 review 内容
                parts = []
                if 'summary' in content and content['summary'].get('value'):
                    parts.append(f"Summary: {content['summary']['value']}")
                if 'strengths' in content:
                    strengths = content['strengths'].get('value', '')
                    if strengths:
                        parts.append(f"Strengths:\n{strengths}")
                if 'weaknesses' in content:
                    weaknesses = content['weaknesses'].get('value', '')
                    if weaknesses:
                        parts.append(f"Weaknesses:\n{weaknesses}")
                if 'questions' in content and content['questions'].get('value'):
                    parts.append(f"Questions: {content['questions']['value']}")
                
                review_data = {
                    'reviewer_id': f"R{i}",
                    'review_id': review_id,
                    'content': "\n\n".join(parts) if parts else "",
                    'summary': content.get('summary', {}).get('value', ''),
                    'strengths': content.get('strengths', {}).get('value', ''),
                    'weaknesses': content.get('weaknesses', {}).get('value', ''),
                    'rating': content.get('rating', {}).get('value', ''),
                    'confidence': content.get('confidence', {}).get('value', ''),
                }
                
                reviews.append(review_data)
                print(f"  [OK] 成功下载，内容长度: {len(review_data['content'])} 字符")
            else:
                print(f"  [FAIL] 失败: Status {response.status_code}")
                
        except Exception as e:
            print(f"  [ERROR] 错误: {e}")
    
    # 保存 reviews
    reviews_path = reviews_dir / f"{paper_id}_reviews.json"
    with open(reviews_path, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    
    print(f"\n保存到: {reviews_path}")
    print(f"总共下载了 {len(reviews)} 个 reviews")

print("\n" + "=" * 60)
print("完成！")

