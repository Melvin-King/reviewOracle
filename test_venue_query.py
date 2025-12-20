import requests
import time
import json

time.sleep(5)
r = requests.get('https://api.openreview.net/notes', 
                params={'content.venue': 'NeurIPS 2024 oral', 'limit': 3}, 
                headers={'User-Agent': 'Mozilla/5.0'})
print('Status:', r.status_code)
if r.status_code == 200:
    data = r.json()
    notes = data.get('notes', [])
    print(f'Found: {len(notes)} papers')
    for n in notes[:3]:
        print(f"  - ID: {n.get('id')}")
        print(f"    Title: {n.get('content', {}).get('title', {}).get('value', 'N/A')[:60]}")
else:
    print('Error:', r.text[:200])

