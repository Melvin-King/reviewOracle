"""检查为什么前几个 reviews 是空的"""
import json
import requests

# 检查 paper_21497 的前几个空 reviews
empty_review_ids = ['CzZnc2zA6V', '1a5PDORc6z', 'qU9a4UHLVY', 'hcOegsgI0b']
base_url = "https://api2.openreview.net"

print("检查空的 review IDs 的 invitation 类型：\n")

for review_id in empty_review_ids:
    try:
        url = f"{base_url}/notes/{review_id}"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            note = response.json()
            invitations = note.get('invitations', [])
            content = note.get('content', {})
            
            print(f"Review ID: {review_id}")
            print(f"  Invitations: {invitations}")
            print(f"  Content keys: {list(content.keys())}")
            
            # 检查是否是 Rebuttal
            if any('Rebuttal' in inv for inv in invitations):
                print(f"  -> 这是 Rebuttal，不是 Official Review!")
            elif any('Official_Review' in inv for inv in invitations):
                print(f"  -> 包含 Official_Review，但可能是 Rebuttal 相关的")
            print()
    except Exception as e:
        print(f"  Error: {e}\n")

