"""修复 reviews 文件，移除空的 Rebuttal entries"""
import json
from pathlib import Path

reviews_dir = Path("data/raw/reviews")

# 需要修复的文件
files_to_fix = [
    'paper_21497_reviews.json',
    'paper_19094_reviews.json',
    'paper_19076_reviews.json'
]

for filename in files_to_fix:
    filepath = reviews_dir / filename
    if not filepath.exists():
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reviews = json.load(f)
    
    # 过滤掉空的 reviews（没有 content 的）
    filtered_reviews = [r for r in reviews if r.get('content', '').strip()]
    
    # 重新编号
    for i, review in enumerate(filtered_reviews, 1):
        review['reviewer_id'] = f"R{i}"
    
    # 保存
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(filtered_reviews, f, ensure_ascii=False, indent=2)
    
    print(f"{filename}: {len(reviews)} -> {len(filtered_reviews)} reviews (移除了 {len(reviews) - len(filtered_reviews)} 个空的)")

print("\n完成！")

