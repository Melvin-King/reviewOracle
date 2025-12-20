import requests
import time
import json

time.sleep(5)
r = requests.get('https://api2.openreview.net/notes', 
                params={
                    'domain': 'NeurIPS.cc/2024/Conference',
                    'content.venue': 'NeurIPS 2024 oral',
                    'limit': 3,
                    'details': 'writable,signatures,invitation',
                    'trash': 'true'
                }, 
                headers={'User-Agent': 'Mozilla/5.0'})

print('Status:', r.status_code)
if r.status_code == 200:
    data = r.json()
    notes = data.get('notes', [])
    print(f'Found: {len(notes)} papers')
    for n in notes[:3]:
        print(f"  - ID: {n.get('id')}")
        print(f"    Title: {n.get('content', {}).get('title', {}).get('value', 'N/A')[:60]}")
        print(f"    Venue: {n.get('content', {}).get('venue', {}).get('value', 'N/A')}")
else:
    print('Error:', r.text[:500])

