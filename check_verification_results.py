"""统计验证结果"""

import json
from pathlib import Path

papers = ['paper_19076', 'paper_19094', 'paper_21497']

total_verified = 0
total_true = 0
total_false = 0
total_partial = 0

print("=" * 70)
print("验证结果统计")
print("=" * 70)
print()

for paper_id in papers:
    file_path = Path(f"data/results/verifications/{paper_id}_verified.json")
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            verifications = json.load(f)
        
        true_count = sum(1 for v in verifications if v['verification_result'] == 'True')
        false_count = sum(1 for v in verifications if v['verification_result'] == 'False')
        partial_count = sum(1 for v in verifications if v['verification_result'] == 'Partially_True')
        
        print(f"{paper_id}:")
        print(f"  总验证数: {len(verifications)}")
        print(f"  True: {true_count}")
        print(f"  False: {false_count}")
        print(f"  Partially_True: {partial_count}")
        print()
        
        total_verified += len(verifications)
        total_true += true_count
        total_false += false_count
        total_partial += partial_count
    else:
        print(f"{paper_id}: 文件不存在")
        print()

print("=" * 70)
print("总计:")
print(f"  总验证数: {total_verified}")
print(f"  True: {total_true} ({total_true/total_verified*100:.1f}%)")
print(f"  False: {total_false} ({total_false/total_verified*100:.1f}%)")
print(f"  Partially_True: {total_partial} ({total_partial/total_verified*100:.1f}%)")
print("=" * 70)

