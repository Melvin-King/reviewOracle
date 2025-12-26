"""
测试 ICLR 2024 API 查询方式
"""

import sys
import io
import requests
import json
import time

# 设置UTF-8编码输出
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

base_url = "https://api2.openreview.net"
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

print("=" * 70)
print("测试 ICLR 2024 API 查询方式")
print("=" * 70)
print()

# 尝试不同的 domain 和 venue 格式
test_configs = [
    {
        "name": "ICLR.cc/2024/Conference",
        "params": {
            "domain": "ICLR.cc/2024/Conference",
            "content.venue": "ICLR 2024",
            "limit": 5,
            "offset": 0,
            "details": "writable,signatures,invitation,presentation,tags",
            "trash": "true"
        }
    },
    {
        "name": "ICLR.cc/2024/Conference (Conference venue)",
        "params": {
            "domain": "ICLR.cc/2024/Conference",
            "content.venue": "ICLR 2024 Conference",
            "limit": 5,
            "offset": 0,
            "details": "writable,signatures,invitation,presentation,tags",
            "trash": "true"
        }
    },
    {
        "name": "ICLR.cc/2024/Conference (Oral)",
        "params": {
            "domain": "ICLR.cc/2024/Conference",
            "content.venue": "ICLR 2024 Conference oral",
            "limit": 5,
            "offset": 0,
            "details": "writable,signatures,invitation,presentation,tags",
            "trash": "true"
        }
    },
    {
        "name": "ICLR.cc/2024/Conference (Poster)",
        "params": {
            "domain": "ICLR.cc/2024/Conference",
            "content.venue": "ICLR 2024 Conference poster",
            "limit": 5,
            "offset": 0,
            "details": "writable,signatures,invitation,presentation,tags",
            "trash": "true"
        }
    },
    {
        "name": "ICLR.cc/2024/Conference (domain only)",
        "params": {
            "domain": "ICLR.cc/2024/Conference",
            "limit": 5,
            "offset": 0,
            "details": "writable,signatures,invitation,presentation,tags",
            "trash": "true"
        }
    }
]

url = f"{base_url}/notes"

for i, config in enumerate(test_configs, 1):
    print(f"\n[{i}/{len(test_configs)}] 测试: {config['name']}")
    print("-" * 70)
    
    try:
        time.sleep(3)
        response = session.get(url, params=config['params'], timeout=30)
        
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 429:
            print(f"  [WARNING] 遇到 429 错误，等待 15 秒...")
            time.sleep(15)
            response = session.get(url, params=config['params'], timeout=30)
            print(f"  重试后状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            notes = data.get('notes', [])
            
            print(f"  找到论文数: {len(notes)}")
            
            if notes:
                print(f"  [SUCCESS] 查询成功！")
                # 显示前几篇论文的信息
                for j, note in enumerate(notes[:3], 1):
                    content = note.get('content', {})
                    title = content.get('title', {})
                    if isinstance(title, dict):
                        title = title.get('value', 'Unknown Title')
                    else:
                        title = str(title)
                    venue = content.get('venue', '')
                    venueid = content.get('venueid', '')
                    
                    print(f"    论文 {j}: {title[:50]}...")
                    print(f"      Venue: {venue}")
                    print(f"      VenueID: {venueid}")
                    print()
                
                # 如果找到论文，可以继续使用这个配置
                print(f"  [INFO] 这个配置可以工作！")
                break
            else:
                print(f"  [INFO] 查询成功但没有返回论文")
        else:
            print(f"  [ERROR] 查询失败")
            try:
                error_data = response.json()
                print(f"  错误信息: {error_data}")
            except:
                print(f"  响应内容: {response.text[:200]}")
                
    except Exception as e:
        print(f"  [ERROR] 异常: {e}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)

