"""详细测试 OpenReview API"""
import requests
import json
import time

base_url = "https://api.openreview.net"

def test_query(name, params):
    print(f"\n[{name}]")
    print(f"参数: {params}")
    time.sleep(3)
    try:
        r = requests.get(f"{base_url}/notes", params=params, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            count = len(data.get('notes', []))
            total_count = data.get('count', 0)
            print(f"返回 notes 数量: {count}")
            print(f"总计数: {total_count}")
            if count > 0:
                note = data['notes'][0]
                print(f"示例论文 ID: {note.get('id')}")
                print(f"标题: {note.get('content', {}).get('title', {}).get('value', 'N/A')[:80]}")
                return True
        else:
            print(f"错误响应: {r.text[:200]}")
    except Exception as e:
        print(f"异常: {e}")
    return False

print("=" * 70)
print("详细测试 OpenReview API - NeurIPS 2024")
print("=" * 70)

# 测试各种查询方式
queries = [
    ("venueid (Conference)", {"content.venueid": "NeurIPS.cc/2024/Conference", "limit": 3}),
    ("venueid (Accepted)", {"content.venueid": "NeurIPS.cc/2024/Conference", "content.venue": "NeurIPS 2024", "limit": 3}),
    ("invitation Submission", {"invitation": "NeurIPS.cc/2024/Conference/-/Submission", "limit": 3}),
    ("invitation Decision", {"invitation": "NeurIPS.cc/2024/Conference/-/Decision", "limit": 3}),
    ("invitation Accepted", {"invitation": "NeurIPS.cc/2024/Conference/-/Accepted", "limit": 3}),
    ("venue 文本", {"content.venue": "NeurIPS 2024", "limit": 3}),
    ("venue 完整", {"content.venue": "NeurIPS.cc/2024/Conference", "limit": 3}),
    ("group + invitation", {"group": "NeurIPS.cc/2024/Conference", "invitation": ".*/-/Submission", "limit": 3}),
]

found = False
for name, params in queries:
    if test_query(name, params):
        found = True
        print(f"\n✓ 成功！使用方式: {name}")
        break

if not found:
    print("\n" + "=" * 70)
    print("所有查询方式都返回空结果")
    print("\n可能的原因：")
    print("1. NeurIPS 2024 论文可能使用不同的 venue 标识")
    print("2. 需要查询特定状态的论文（如 Decision 或 Accepted）")
    print("3. API 可能需要认证或特殊权限")
    print("4. 数据可能还没有完全同步到 API")
    print("\n建议：")
    print("- 访问 https://openreview.net/group?id=NeurIPS.cc/2024/Conference 查看实际数据")
    print("- 检查网页上的论文 venue 字段是什么格式")
    print("- 或者手动准备数据文件")

