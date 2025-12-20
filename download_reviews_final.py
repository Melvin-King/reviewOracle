"""最终尝试下载 reviews - 等待足够长时间"""
import sys
sys.path.insert(0, '.')
import requests
import json
import time
from pathlib import Path
from datetime import datetime

base_url = "https://api2.openreview.net"
reviews_dir = Path("data/raw/reviews")
reviews_dir.mkdir(parents=True, exist_ok=True)

# 论文信息
papers = [
    ('paper_21497', 'aVh9KRZdRk'),
    ('paper_19094', 'REIK4SZMJt'),
    ('paper_19076', 'gojL67CfS8'),
]

print("=" * 70)
print("下载 Reviews - 最终尝试")
print("=" * 70)
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

for i, (paper_id, forum_id) in enumerate(papers, 1):
    print(f"\n{'='*70}")
    print(f"论文 {i}/{len(papers)}: {paper_id} (Forum: {forum_id})")
    print(f"{'='*70}")
    
    if i > 1:
        wait_minutes = 3
        print(f"\n等待 {wait_minutes} 分钟以避免 API 限制...")
        time.sleep(wait_minutes * 60)
    
    # 获取 forum 下的所有 notes
    url = f"{base_url}/notes"
    params = {
        "domain": "NeurIPS.cc/2024/Conference",
        "forum": forum_id,
        "details": "writable,signatures,invitation,presentation,tags",
        "trash": "true",
        "limit": 1000
    }
    
    print(f"\n发送请求...")
    try:
        response = requests.get(url, params=params, timeout=60, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            all_notes = data.get('notes', [])
            print(f"获取到 {len(all_notes)} 个 notes")
            
            # 过滤出 Official Review
            reviews = []
            for note in all_notes:
                invitations = note.get('invitations', [])
                if isinstance(invitations, str):
                    invitations = [invitations]
                elif not isinstance(invitations, list):
                    invitations = []
                
                if any('Official_Review' in inv for inv in invitations):
                    content = note.get('content', {})
                    
                    # 构建完整的 review 内容
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
                    if 'limitations' in content and content['limitations'].get('value'):
                        parts.append(f"Limitations: {content['limitations']['value']}")
                    
                    review_data = {
                        'reviewer_id': f"R{len(reviews)+1}",
                        'review_id': note.get('id', ''),
                        'content': "\n\n".join(parts) if parts else "",
                        'summary': content.get('summary', {}).get('value', ''),
                        'strengths': content.get('strengths', {}).get('value', ''),
                        'weaknesses': content.get('weaknesses', {}).get('value', ''),
                        'rating': content.get('rating', {}).get('value', ''),
                        'confidence': content.get('confidence', {}).get('value', ''),
                    }
                    reviews.append(review_data)
            
            print(f"过滤出 {len(reviews)} 个 Official Reviews")
            
            # 保存
            reviews_path = reviews_dir / f"{paper_id}_reviews.json"
            with open(reviews_path, 'w', encoding='utf-8') as f:
                json.dump(reviews, f, ensure_ascii=False, indent=2)
            
            print(f"保存到: {reviews_path}")
            
            if reviews:
                for r in reviews:
                    print(f"  - {r['reviewer_id']}: {len(r['content'])} 字符, Rating: {r.get('rating', 'N/A')}")
        elif response.status_code == 429:
            print(f"[ERROR] 429 错误 - API 频率限制")
            print(f"建议：等待 10-15 分钟后重试")
        else:
            print(f"[ERROR] 错误: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"[ERROR] 异常: {e}")

print(f"\n{'='*70}")
print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*70}")

