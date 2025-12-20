"""
手动下载论文和 review 的辅助工具
如果 OpenReview API 不可用，可以使用这个工具手动准备数据
"""

import json
from pathlib import Path
from typing import List, Dict


class ManualDataPreparer:
    """手动数据准备工具"""
    
    def __init__(self, download_path: str = "data/raw"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)
    
    def create_review_template(self, paper_id: str, num_reviews: int = 3):
        """
        创建 review 模板文件
        
        Args:
            paper_id: 论文 ID
            num_reviews: review 数量
        """
        reviews_dir = self.download_path / "reviews"
        reviews_dir.mkdir(parents=True, exist_ok=True)
        
        reviews = []
        for i in range(num_reviews):
            review = {
                'reviewer_id': f"R{i+1}",
                'review_id': f"{paper_id}_review_{i+1}",
                'content': f"这是 {paper_id} 的第 {i+1} 个 review。\n\n请在这里填写实际的 review 内容。",
                'summary': '',
                'strengths': '',
                'weaknesses': '',
                'rating': '',
                'confidence': ''
            }
            reviews.append(review)
        
        reviews_path = reviews_dir / f"{paper_id}_reviews.json"
        with open(reviews_path, 'w', encoding='utf-8') as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] 已创建 review 模板: {reviews_path}")
        print(f"[INFO] 请手动编辑此文件，填入实际的 review 内容")
        return reviews_path
    
    def prepare_manual_data(self, paper_ids: List[str]):
        """
        为多篇论文准备手动数据模板
        
        Args:
            paper_ids: 论文 ID 列表
        """
        for paper_id in paper_ids:
            self.create_review_template(paper_id)
        
        print(f"\n[INFO] 已为 {len(paper_ids)} 篇论文创建 review 模板")
        print(f"[INFO] 请手动：")
        print(f"  1. 将 PDF 文件放到 data/raw/papers/ 目录")
        print(f"  2. 编辑 data/raw/reviews/ 目录下的 JSON 文件，填入实际的 review 内容")


if __name__ == "__main__":
    preparer = ManualDataPreparer()
    # 示例：为 3 篇论文创建模板
    preparer.prepare_manual_data(["paper_001", "paper_002", "paper_003"])

