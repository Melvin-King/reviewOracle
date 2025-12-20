"""详细测试 OpenReview API - 查找已接受的论文"""
import requests
import json
import time

base_url = "https://api.openreview.net"

print("=" * 60)
print("详细测试 - 查找 NeurIPS 2024 已接受的论文")
print("=" * 60)

# 关键发现：可能需要查询 Decision 或者已接受的论文
# 已接受的论文 venue 可能是 "NeurIPS 2024" 而不是在 Submission 中

test_queries = [
    {
        "name": "查询 Decision",
        "params": {
            "invitation": "NeurIPS.cc/2024/Conference/-/Decision",
            "limit": 5
        }
    },
    {
        "name": "查询所有 notes（无过滤）",
        "params": {
            "group": "NeurIPS.cc/2024/Conference",
            "limit": 10
        }
    },
    {
        "name": "查询 venue 包含 NeurIPS 2024",
        "params": {
            "content.venue": "NeurIPS 2024",
            "limit": 5
        }
    },
    {
        "name": "查询 venueid 且包含 Decision",
        "params": {
            "content.venueid": "NeurIPS.cc/2024/Conference",
            "invitation": "NeurIPS.cc/2024/Conference/-/Decision",
            "limit": 5
        }
    },
    {
        "name": "直接访问一篇已知论文（如果有）",
        "params": {
            "id": "NeurIPS.cc/2024/Conference/Submission1"  # 示例 ID
        }
    }
]

for i, test in enumerate(test_queries, 1):
    print(f"\n[测试 {i}] {test['name']}")
    time.sleep(3)  # 避免 429
    try:
        r = requests.get(f"{base_url}/notes", params=test['params'], 
                        headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            notes = data.get('notes', [])
            print(f"  找到 {len(notes)} 条记录")
            
            if notes:
                note = notes[0]
                print(f"  示例记录:")
                print(f"    ID: {note.get('id', 'N/A')}")
                print(f"    Invitation: {note.get('invitation', 'N/A')}")
                if 'content' in note:
                    content = note['content']
                    print(f"    Title: {content.get('title', {}).get('value', 'N/A')[:60]}")
                    print(f"    Venue: {content.get('venue', {}).get('value', 'N/A')}")
                    print(f"    VenueID: {content.get('venueid', {}).get('value', 'N/A')}")
        else:
            print(f"  错误响应: {r.text[:200]}")
    except Exception as e:
        print(f"  异常: {e}")

# 尝试直接访问 OpenReview 网页看看实际的数据结构
print("\n" + "=" * 60)
print("提示：如果以上都返回空，可能需要：")
print("1. 直接访问 https://openreview.net/group?id=NeurIPS.cc/2024/Conference")
print("2. 查看网页上论文的实际 venue 字段")
print("3. 或者论文可能还在不同的 invitation 下")

