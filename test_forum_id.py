import requests
import time
import json

# 从网页上看到的 forum ID
forum_ids = ['aVh9KRZdRk', 'REIK4SZMJt', 'gojL67CfS8']

print("测试通过 forum ID 查询...")
for forum_id in forum_ids:
    time.sleep(3)
    r = requests.get('https://api.openreview.net/notes', 
                    params={'forum': forum_id}, 
                    headers={'User-Agent': 'Mozilla/5.0'})
    print(f'\nForum ID: {forum_id}')
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        notes = data.get('notes', [])
        print(f'Found: {len(notes)} notes')
        if notes:
            note = notes[0]
            print(f"  ID: {note.get('id')}")
            print(f"  Invitation: {note.get('invitation', 'N/A')}")
            print(f"  Venue: {note.get('content', {}).get('venue', {}).get('value', 'N/A')}")
            print(f"  Title: {note.get('content', {}).get('title', {}).get('value', 'N/A')[:60]}")
            break

