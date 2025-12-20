"""调试 reviews API 返回的数据结构"""
import requests
import time
import json

forum_id = 'aVh9KRZdRk'
url = 'https://api2.openreview.net/notes'

params = {
    "count": "true",
    "domain": "NeurIPS.cc/2024/Conference",
    "forum": forum_id,
    "details": "writable,signatures,invitation,presentation,tags",
    "trash": "true",
    "limit": 1000
}

print("等待 120 秒...")
time.sleep(120)

response = requests.get(url, params=params, timeout=60, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

if response.status_code == 200:
    data = response.json()
    notes = data.get('notes', [])
    print(f"\n获取到 {len(notes)} 个 notes\n")
    
    # 检查第一个 note 的完整结构
    if notes:
        first_note = notes[0]
        print("第一个 note 的键:")
        print(list(first_note.keys()))
        print("\n第一个 note 的完整内容（前 2000 字符）:")
        print(json.dumps(first_note, indent=2, ensure_ascii=False)[:2000])
        
        # 查找包含 "Review" 的 notes
        print("\n查找包含 'Review' 的 notes:")
        for i, note in enumerate(notes):
            note_str = json.dumps(note, ensure_ascii=False).lower()
            if 'review' in note_str or 'official' in note_str:
                print(f"\nNote {i+1}:")
                print(f"  ID: {note.get('id')}")
                # 尝试不同的方式获取 invitation
                invitation = note.get('invitation') or note.get('invitations') or note.get('details', {}).get('invitation')
                print(f"  Invitation: {invitation}")
                if 'content' in note:
                    content_keys = list(note['content'].keys())
                    print(f"  Content keys: {content_keys}")
                    if 'summary' in note['content']:
                        print(f"  Summary: {note['content']['summary'].get('value', '')[:100]}")
else:
    print(f"错误: {response.status_code}")
    print(response.text[:500])

