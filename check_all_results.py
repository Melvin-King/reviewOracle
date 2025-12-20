"""检查所有步骤的处理结果"""

import json
from pathlib import Path

papers = ['paper_19076', 'paper_19094', 'paper_21497']

print("=" * 70)
print("Pipeline 处理结果总结")
print("=" * 70)
print()

# Step 1: Claims
print("Step 1: 观点提取 (Claims Extraction)")
print("-" * 70)
for paper_id in papers:
    file_path = Path(f"data/processed/extracted/{paper_id}_claims.json")
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            claims = json.load(f)
        print(f"  {paper_id}: {len(claims)} claims")
    else:
        print(f"  {paper_id}: 未找到")
print()

# Step 2: Verifications
print("Step 2: 事实验证 (Fact Verification)")
print("-" * 70)
total_verified = 0
for paper_id in papers:
    file_path = Path(f"data/results/verifications/{paper_id}_verified.json")
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            verifications = json.load(f)
        true_count = sum(1 for v in verifications if v['verification_result'] == 'True')
        false_count = sum(1 for v in verifications if v['verification_result'] == 'False')
        partial_count = sum(1 for v in verifications if v['verification_result'] == 'Partially_True')
        print(f"  {paper_id}: {len(verifications)} verified (T:{true_count}, F:{false_count}, P:{partial_count})")
        total_verified += len(verifications)
    else:
        print(f"  {paper_id}: 未找到")
print(f"  总计: {total_verified} verified claims")
print()

# Step 3: Weights
print("Step 3: 权重计算 (Weight Calculation)")
print("-" * 70)
for paper_id in papers:
    file_path = Path(f"data/results/weights/{paper_id}_weights.json")
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            weights = json.load(f)
        print(f"  {paper_id}: {len(weights)} reviewers")
        for reviewer_id, data in weights.items():
            print(f"    - {reviewer_id}: weight={data['weight']:.3f}")
    else:
        print(f"  {paper_id}: 未找到")
print()

# Step 4: Reports
print("Step 4: 合成报告 (Synthesis Report)")
print("-" * 70)
for paper_id in papers:
    file_path = Path(f"data/results/synthesis/{paper_id}_report.md")
    if file_path.exists():
        file_size = file_path.stat().st_size
        print(f"  {paper_id}: {file_size:,} bytes - {file_path}")
    else:
        print(f"  {paper_id}: 未找到")
print()

print("=" * 70)
print("所有步骤处理完成！")
print("=" * 70)

