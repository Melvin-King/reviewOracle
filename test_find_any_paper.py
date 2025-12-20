"""尝试找到任何 NeurIPS 2024 相关的论文"""
import requests
import json
import time

base_url = "https://api.openreview.net"

print("尝试找到 NeurIPS 2024 的任何论文...\n")

# 方法 1: 查询所有包含 "2024" 的 notes
print("[方法 1] 查询所有包含 'NeurIPS' 和 '2024' 的 notes")
time.sleep(5)
try:
    # 尝试使用正则或模糊查询
    r = requests.get(f"{base_url}/notes", params={
        "content.venue": ".*2024.*",
        "limit": 10
    }, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"找到 {len(data.get('notes', []))} 条记录")
        for note in data.get('notes', [])[:3]:
            venue = note.get('content', {}).get('venue', {}).get('value', 'N/A')
            print(f"  Venue: {venue}")
except Exception as e:
    print(f"错误: {e}")

# 方法 2: 直接访问网页看看实际的论文 ID 格式
print("\n[方法 2] 检查是否需要查询 Camera_Ready 或 Final 版本")
time.sleep(5)
try:
    r = requests.get(f"{base_url}/notes", params={
        "invitation": "NeurIPS.cc/2024/Conference/-/Camera_Ready_Revision",
        "limit": 3
    }, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"找到 {len(data.get('notes', []))} 条记录")
        if data.get('notes'):
            note = data['notes'][0]
            print(f"  论文 ID: {note.get('id')}")
            print(f"  标题: {note.get('content', {}).get('title', {}).get('value', 'N/A')[:60]}")
except Exception as e:
    print(f"错误: {e}")

# 方法 3: 检查 2023 年的格式，看看有什么不同
print("\n[方法 3] 检查 2023 年的数据格式（作为参考）")
time.sleep(5)
try:
    r = requests.get(f"{base_url}/notes", params={
        "content.venueid": "NeurIPS.cc/2023/Conference",
        "limit": 1
    }, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        notes = data.get('notes', [])
        print(f"找到 {len(notes)} 条记录")
        if notes:
            note = notes[0]
            print(f"  论文 ID: {note.get('id')}")
            print(f"  Venue: {note.get('content', {}).get('venue', {}).get('value', 'N/A')}")
            print(f"  VenueID: {note.get('content', {}).get('venueid', {}).get('value', 'N/A')}")
            print(f"  Invitation: {note.get('invitation', 'N/A')}")
except Exception as e:
    print(f"错误: {e}")

print("\n" + "=" * 70)
print("如果所有方法都返回空，可能的原因：")
print("1. NeurIPS 2024 论文在 OpenReview 上但使用不同的标识")
print("2. 需要登录或特殊权限才能访问")
print("3. 数据可能还没有同步到公开 API")
print("\n建议：直接访问 https://openreview.net/group?id=NeurIPS.cc/2024/Conference")
print("查看网页上实际显示的论文，然后手动准备数据")

