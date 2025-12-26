"""检查论文的最终决策状态（Accept/Reject）"""

import sys
import io
import requests
import json
from pathlib import Path

# 设置UTF-8编码输出
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 论文信息：paper_id -> forum_id
papers = {
    'paper_19076': 'gojL67CfS8',
    'paper_19094': 'REIK4SZMJt',
    'paper_21497': 'aVh9KRZdRk'
}

base_url = "https://api2.openreview.net"

print("=" * 70)
print("检查论文最终决策状态")
print("=" * 70)
print()

for paper_id, forum_id in papers.items():
    print(f"论文: {paper_id} (Forum ID: {forum_id})")
    print("-" * 70)
    
    try:
        # 获取论文信息
        url = f"{base_url}/notes"
        params = {
            "id": forum_id,
            "details": "writable,signatures,invitation,presentation,tags"
        }
        
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            notes = data.get('notes', [])
            
            if notes:
                note = notes[0]
                
                # 检查决策信息
                content = note.get('content', {})
                decision = content.get('decision', '')
                venue = content.get('venue', '')
                venueid = content.get('venueid', '')
                
                # 检查标签（可能包含决策信息）
                tags = note.get('tags', [])
                
                print(f"  Title: {content.get('title', 'N/A')[:60]}...")
                print(f"  Venue: {venue}")
                print(f"  Venue ID: {venueid}")
                
                if decision:
                    print(f"  Decision: {decision}")
                else:
                    print(f"  Decision: 未找到决策信息")
                
                if tags:
                    print(f"  Tags: {tags}")
                
                # 检查venueid是否包含"Accepted"或"Rejected"
                if 'Accepted' in venueid or 'Accepted' in venue:
                    print(f"  [ACCEPTED] 状态: ACCEPTED")
                elif 'Rejected' in venueid or 'Rejected' in venue:
                    print(f"  [REJECTED] 状态: REJECTED")
                elif 'Withdrawn' in venueid or 'Withdrawn' in venue:
                    print(f"  [WITHDRAWN] 状态: WITHDRAWN")
                else:
                    print(f"  [UNKNOWN] 状态: 未知（可能是未发布决策）")
                
            else:
                print(f"  [ERROR] 未找到论文信息")
        else:
            print(f"  [ERROR] API 请求失败: {response.status_code}")
    
    except Exception as e:
        print(f"  [ERROR] 错误: {e}")
    
    print()

print("=" * 70)
print("检查完成")
print("=" * 70)
print("\n提示：如果显示'未知'，可能是因为决策信息尚未公开，")
print("或者需要登录OpenReview账户才能查看。")

