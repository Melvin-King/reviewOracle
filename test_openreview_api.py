"""测试 OpenReview API 调用"""
import requests
import json
import time

base_url = "https://api.openreview.net"

print("=" * 60)
print("测试 OpenReview API")
print("=" * 60)

# 测试 1: 使用 venueid
print("\n[测试 1] 使用 content.venueid")
time.sleep(5)
try:
    r = requests.get(f"{base_url}/notes", params={
        "content.venueid": "NeurIPS.cc/2024/Conference",
        "limit": 3
    }, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"找到 {len(data.get('notes', []))} 篇论文")
        if data.get('notes'):
            print(f"第一篇论文: {data['notes'][0].get('content', {}).get('title', {}).get('value', 'N/A')[:60]}")
    else:
        print(f"响应: {r.text[:200]}")
except Exception as e:
    print(f"错误: {e}")

# 测试 2: 使用 invitation
print("\n[测试 2] 使用 invitation")
time.sleep(5)
try:
    r = requests.get(f"{base_url}/notes", params={
        "invitation": "NeurIPS.cc/2024/Conference/-/Submission",
        "limit": 3
    }, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"找到 {len(data.get('notes', []))} 篇论文")
        if data.get('notes'):
            print(f"第一篇论文: {data['notes'][0].get('content', {}).get('title', {}).get('value', 'N/A')[:60]}")
    else:
        print(f"响应: {r.text[:200]}")
except Exception as e:
    print(f"错误: {e}")

# 测试 3: 使用 group
print("\n[测试 3] 使用 group (通过 /groups 端点)")
time.sleep(5)
try:
    r = requests.get(f"{base_url}/groups", params={
        "id": "NeurIPS.cc/2024/Conference"
    }, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Group 数据: {json.dumps(data, indent=2)[:500]}")
except Exception as e:
    print(f"错误: {e}")

# 测试 4: 直接搜索 2023 年看看格式
print("\n[测试 4] 测试 2023 年（确认 API 是否可用）")
time.sleep(5)
try:
    r = requests.get(f"{base_url}/notes", params={
        "content.venueid": "NeurIPS.cc/2023/Conference",
        "limit": 1
    }, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"找到 {len(data.get('notes', []))} 篇论文")
        if data.get('notes'):
            note = data['notes'][0]
            print(f"论文 ID: {note.get('id')}")
            print(f"标题: {note.get('content', {}).get('title', {}).get('value', 'N/A')[:60]}")
except Exception as e:
    print(f"错误: {e}")

print("\n" + "=" * 60)

