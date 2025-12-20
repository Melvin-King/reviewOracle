"""
统一的数据加载接口
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from .pdf_parser import PDFParser


class DataLoader:
    """数据加载器"""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.pdf_parser = PDFParser()
    
    def load_paper_text(self, paper_id: str, use_cache: bool = True) -> str:
        """
        加载论文文本
        
        Args:
            paper_id: 论文 ID
            use_cache: 是否使用缓存的解析结果
            
        Returns:
            论文文本内容
        """
        # 先检查是否有缓存的文本
        cached_path = self.base_path / "processed" / "papers" / f"{paper_id}.txt"
        if use_cache and cached_path.exists():
            with open(cached_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # 解析 PDF
        pdf_path = self.base_path / "raw" / "papers" / f"{paper_id}.pdf"
        if not pdf_path.exists():
            raise FileNotFoundError(f"论文 PDF 不存在: {pdf_path}")
        
        text = self.pdf_parser.parse_pdf(str(pdf_path))
        text = self.pdf_parser.clean_text(text)
        
        # 缓存结果
        cached_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cached_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return text
    
    def load_reviews(self, paper_id: str) -> List[Dict]:
        """
        加载 review 数据
        
        Args:
            paper_id: 论文 ID
            
        Returns:
            Review 列表
        """
        reviews_path = self.base_path / "raw" / "reviews" / f"{paper_id}_reviews.json"
        if not reviews_path.exists():
            return []
        
        with open(reviews_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_claims(self, paper_id: str) -> List[Dict]:
        """
        加载已提取的观点（Step 1 的输出）
        
        Args:
            paper_id: 论文 ID
            
        Returns:
            观点列表
        """
        claims_path = self.base_path / "processed" / "extracted" / f"{paper_id}_claims.json"
        if not claims_path.exists():
            return []
        
        with open(claims_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_claims(self, paper_id: str, claims: List[Dict]):
        """保存提取的观点"""
        claims_path = self.base_path / "processed" / "extracted" / f"{paper_id}_claims.json"
        claims_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(claims_path, 'w', encoding='utf-8') as f:
            json.dump(claims, f, ensure_ascii=False, indent=2)
    
    def load_verifications(self, paper_id: str) -> Dict[str, Dict]:
        """
        加载验证结果（Step 2 的输出）
        
        Args:
            paper_id: 论文 ID
            
        Returns:
            验证结果字典，key 为 claim_id
        """
        verifications_path = self.base_path / "results" / "verifications" / f"{paper_id}_verified.json"
        if not verifications_path.exists():
            return {}
        
        try:
            with open(verifications_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 转换为字典格式，key 为 claim_id
                if isinstance(data, list):
                    return {item['id']: item for item in data}
                elif isinstance(data, dict):
                    return data
                else:
                    return {}
        except json.JSONDecodeError as e:
            print(f"[ERROR] 解析验证结果文件失败: {e}")
            return {}
    
    def load_weights(self, paper_id: str) -> Dict[str, float]:
        """
        加载权重结果（Step 3 的输出）
        
        Args:
            paper_id: 论文 ID
            
        Returns:
            权重字典，key 为 reviewer_id
        """
        weights_path = self.base_path / "results" / "weights" / f"{paper_id}_weights.json"
        if not weights_path.exists():
            return {}
        
        try:
            with open(weights_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] 解析权重文件失败: {e}")
            return {}

