"""分析论文状态（基于review rating）"""

import json
from pathlib import Path

papers = ['paper_19076', 'paper_19094', 'paper_21497']

print("=" * 70)
print("基于 Review Rating 分析论文状态")
print("=" * 70)
print()
print("说明：")
print("- NeurIPS 通常 rating >= 6 倾向于 Accept")
print("- Rating < 6 倾向于 Reject")
print("- 但最终决策还取决于其他因素")
print()

for paper_id in papers:
    file_path = Path(f"data/raw/reviews/{paper_id}_reviews.json")
    if not file_path.exists():
        print(f"{paper_id}: 未找到review文件")
        continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reviews = json.load(f)
    
    print(f"论文: {paper_id}")
    print("-" * 70)
    
    ratings = []
    for review in reviews:
        rating = review.get('rating', None)
        reviewer_id = review.get('reviewer_id', 'Unknown')
        if rating is not None:
            ratings.append(rating)
            print(f"  {reviewer_id}: Rating = {rating}")
    
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
        min_rating = min(ratings)
        max_rating = max(ratings)
        
        print(f"\n  Rating 统计:")
        print(f"    平均: {avg_rating:.2f}")
        print(f"    范围: {min_rating} - {max_rating}")
        
        # 根据rating推断状态
        if avg_rating >= 6.5:
            print(f"    推断: 很可能 ACCEPTED (平均rating >= 6.5)")
        elif avg_rating >= 6.0:
            print(f"    推断: 可能 ACCEPTED (平均rating >= 6.0)")
        elif avg_rating >= 5.0:
            print(f"    推断: 不确定 (平均rating 5.0-6.0)")
        else:
            print(f"    推断: 可能 REJECTED (平均rating < 5.0)")
    else:
        print("  未找到rating信息")
    
    print()

print("=" * 70)
print("注意：这只是基于rating的推断，实际决策可能不同")
print("=" * 70)


