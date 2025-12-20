"""
Step 3: Bias Calculation & Weighting (偏差计算与加权层)
计算 Reviewer 的可信度权重
"""

from typing import List, Dict
from collections import defaultdict


class WeightingAgent:
    """偏差计算与加权 Agent"""
    
    def __init__(self, alpha: float = 0.5, beta: float = 0.5):
        """
        Args:
            alpha: Hollowness 惩罚系数
            beta: Hallucination 惩罚系数
        """
        self.alpha = alpha
        self.beta = beta
    
    def calculate_hollowness(self, reviewer_claims: List[Dict]) -> float:
        """
        计算空洞指数（Hollowness）
        即 substantiation_type == None 的占比
        
        Args:
            reviewer_claims: 某个 Reviewer 的所有观点
            
        Returns:
            空洞指数（0-1）
        """
        if not reviewer_claims:
            return 1.0  # 如果没有观点，认为完全空洞
        
        none_count = sum(
            1 for claim in reviewer_claims
            if not claim.get('substantiation_type') or claim.get('substantiation_type') == 'None'
        )
        
        return none_count / len(reviewer_claims)
    
    def calculate_hallucination(self, reviewer_claims: List[Dict], 
                               verifications: Dict[str, Dict]) -> float:
        """
        计算幻觉指数（Hallucination）
        即 verification_result == False 的占比
        
        Args:
            reviewer_claims: 某个 Reviewer 的所有观点
            verifications: 验证结果字典，key 为 claim_id
            
        Returns:
            幻觉指数（0-1）
        """
        if not reviewer_claims:
            return 0.0
        
        # 只考虑有证据的观点（需要验证的）
        claims_to_check = [
            claim for claim in reviewer_claims
            if claim.get('substantiation_type') and claim.get('substantiation_type') != 'None'
        ]
        
        if not claims_to_check:
            return 0.0  # 如果没有需要验证的观点，幻觉指数为0
        
        false_count = 0
        for claim in claims_to_check:
            claim_id = claim.get('id')
            if claim_id in verifications:
                if verifications[claim_id].get('verification_result') == 'False':
                    false_count += 1
        
        return false_count / len(claims_to_check)
    
    def calculate_weight(self, reviewer_id: str, claims: List[Dict], 
                        verifications: Dict[str, Dict]) -> float:
        """
        计算 Reviewer 的最终权重
        
        公式：Weight(R) = 1.0 - (α × Hollowness + β × Hallucination)
        
        Args:
            reviewer_id: Reviewer ID
            claims: 该 Reviewer 的所有观点
            verifications: 验证结果字典
            
        Returns:
            权重（0-1）
        """
        hollowness = self.calculate_hollowness(claims)
        hallucination = self.calculate_hallucination(claims, verifications)
        
        bias_index = self.alpha * hollowness + self.beta * hallucination
        weight = 1.0 - bias_index
        
        # 确保权重在 [0, 1] 范围内
        weight = max(0.0, min(1.0, weight))
        
        return weight
    
    def process_all_reviewers(self, claims: List[Dict], 
                             verifications: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        处理所有 Reviewers，计算每个的权重和详细指标
        
        Args:
            claims: 所有观点列表
            verifications: 验证结果字典
            
        Returns:
            权重字典，包含每个 reviewer 的权重和详细指标
        """
        # 按 reviewer 分组
        reviewer_claims = defaultdict(list)
        for claim in claims:
            # 从 claim id 提取 reviewer_id（格式：R1-C1 -> R1）
            claim_id = claim.get('id', '')
            if '-' in claim_id:
                reviewer_id = claim_id.split('-')[0]
                reviewer_claims[reviewer_id].append(claim)
        
        results = {}
        
        for reviewer_id, reviewer_claim_list in reviewer_claims.items():
            hollowness = self.calculate_hollowness(reviewer_claim_list)
            hallucination = self.calculate_hallucination(reviewer_claim_list, verifications)
            weight = self.calculate_weight(reviewer_id, reviewer_claim_list, verifications)
            
            results[reviewer_id] = {
                'weight': weight,
                'hollowness': hollowness,
                'hallucination': hallucination,
                'num_claims': len(reviewer_claim_list),
                'num_claims_with_evidence': sum(
                    1 for c in reviewer_claim_list
                    if c.get('substantiation_type') and c.get('substantiation_type') != 'None'
                ),
                'num_false_claims': sum(
                    1 for c in reviewer_claim_list
                    if c.get('id') in verifications and 
                    verifications[c.get('id')].get('verification_result') == 'False'
                )
            }
        
        return results

