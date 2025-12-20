import requests
import time
import json

# 尝试搜索 API
print("尝试搜索 API...")
time.sleep(5)

# 方法1: 使用搜索端点
r = requests.get('https://api.openreview.net/notes', 
                params={
                    'content.title': 'Learning to grok',  # 从网页上看到的标题
                    'limit': 5
                }, 
                headers={'User-Agent': 'Mozilla/5.0'})

print(f'Search by title - Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'Found: {len(data.get("notes", []))} notes')
    if data.get('notes'):
        note = data['notes'][0]
        print(f"  ID: {note.get('id')}")
        print(f"  Venue: {note.get('content', {}).get('venue', {}).get('value', 'N/A')}")

# 方法2: 尝试查询所有已发布的 notes（可能有不同的参数）
time.sleep(5)
print("\n尝试查询所有 notes（无过滤）...")
r2 = requests.get('https://api.openreview.net/notes', 
                 params={'limit': 10}, 
                 headers={'User-Agent': 'Mozilla/5.0'})
print(f'All notes - Status: {r2.status_code}')
if r2.status_code == 200:
    data2 = r2.json()
    print(f'Found: {len(data2.get("notes", []))} notes')
    # 查看是否有 NeurIPS 相关的
    for note in data2.get('notes', [])[:5]:
        venue = note.get('content', {}).get('venue', {}).get('value', '')
        if 'NeurIPS' in venue or '2024' in venue:
            print(f"  Found NeurIPS note: {note.get('id')}, Venue: {venue}")

