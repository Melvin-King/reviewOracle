import requests
import time
import json

# forum ID（从网页 URL 中获取）
forum_id = 'aVh9KRZdRk'

print(f"查询 forum {forum_id} 下的所有 notes...")
time.sleep(5)

# 查询 forum 下的所有 notes
r = requests.get('https://api.openreview.net/notes', 
                params={
                    'forum': forum_id,
                    'details': 'replyCount,invitation,original'
                }, 
                headers={'User-Agent': 'Mozilla/5.0'})

print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    notes = data.get('notes', [])
    print(f'Found: {len(notes)} notes in forum')
    
    for i, note in enumerate(notes):
        print(f"\nNote {i+1}:")
        print(f"  ID: {note.get('id')}")
        print(f"  Invitation: {note.get('invitation', 'N/A')}")
        if 'content' in note:
            content = note['content']
            if 'title' in content:
                print(f"  Title: {content['title'].get('value', 'N/A')[:60]}")
            if 'venue' in content:
                print(f"  Venue: {content['venue'].get('value', 'N/A')}")
            if 'review' in content:
                print(f"  Review: {content['review'].get('value', 'N/A')[:60]}")
else:
    print(f'Error: {r.text[:500]}')

