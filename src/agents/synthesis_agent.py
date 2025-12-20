"""
Step 4: Meta-Review Synthesis (合成决策层)
基于加权后的观点生成最终报告
"""

from typing import List, Dict
from collections import defaultdict


class SynthesisAgent:
    """合成决策 Agent"""
    
    def __init__(self, accept_threshold: float = 0.6, topics: List[str] = None):
        """
        Args:
            accept_threshold: 接受阈值
            topics: 主题列表
        """
        self.accept_threshold = accept_threshold
        self.topics = topics or ["Novelty", "Experiments", "Writing", "Significance", "Reproducibility"]
    
    def sentiment_to_score(self, sentiment: str) -> float:
        """
        将情感转换为分数
        
        Args:
            sentiment: Positive, Negative, Neutral
            
        Returns:
            分数：Positive -> 1.0, Negative -> -1.0, Neutral -> 0.0
        """
        sentiment_lower = sentiment.lower()
        if 'positive' in sentiment_lower:
            return 1.0
        elif 'negative' in sentiment_lower:
            return -1.0
        else:
            return 0.0
    
    def filter_false_claims(self, claims: List[Dict], verifications: Dict[str, Dict]) -> List[Dict]:
        """
        过滤掉验证结果为 False 的观点
        
        Args:
            claims: 所有观点列表
            verifications: 验证结果字典
            
        Returns:
            过滤后的观点列表
        """
        filtered_claims = []
        for claim in claims:
            claim_id = claim.get('id')
            # 如果没有验证结果，保留该观点
            if claim_id not in verifications:
                filtered_claims.append(claim)
            else:
                # 只保留验证结果不是 False 的观点
                verification_result = verifications[claim_id].get('verification_result')
                if verification_result != 'False':
                    filtered_claims.append(claim)
        
        return filtered_claims
    
    def weighted_voting(self, topic: str, claims: List[Dict], weights: Dict[str, Dict]) -> Dict:
        """
        对某个主题进行加权投票
        
        公式：Score(Topic) = Σ (Reviewer_Sentiment × Weight(R))
        
        Args:
            topic: 主题名称
            claims: 该主题的所有观点（已过滤错误观点）
            weights: 权重字典
            
        Returns:
            包含分数和详细信息的字典
        """
        topic_claims = [c for c in claims if c.get('topic', '').lower() == topic.lower()]
        
        if not topic_claims:
            return {
                'topic': topic,
                'score': 0.0,
                'num_claims': 0,
                'weighted_sum': 0.0,
                'decision': 'Neutral'
            }
        
        weighted_sum = 0.0
        total_weight = 0.0
        claim_details = []
        
        for claim in topic_claims:
            # 获取 reviewer_id
            claim_id = claim.get('id', '')
            reviewer_id = claim_id.split('-')[0] if '-' in claim_id else 'Unknown'
            
            # 获取权重
            reviewer_weight = weights.get(reviewer_id, {}).get('weight', 0.0)
            
            # 获取情感分数
            sentiment = claim.get('sentiment', 'Neutral')
            sentiment_score = self.sentiment_to_score(sentiment)
            
            # 计算加权贡献
            contribution = sentiment_score * reviewer_weight
            weighted_sum += contribution
            total_weight += reviewer_weight
            
            claim_details.append({
                'claim_id': claim_id,
                'reviewer_id': reviewer_id,
                'statement': claim.get('statement', ''),
                'sentiment': sentiment,
                'sentiment_score': sentiment_score,
                'reviewer_weight': reviewer_weight,
                'contribution': contribution
            })
        
        # 计算最终分数（归一化）
        if total_weight > 0:
            score = weighted_sum / total_weight
        else:
            score = 0.0
        
        # 决策
        if score >= self.accept_threshold:
            decision = 'Accept'
        elif score <= -self.accept_threshold:
            decision = 'Reject'
        else:
            decision = 'Neutral'
        
        return {
            'topic': topic,
            'score': score,
            'num_claims': len(topic_claims),
            'weighted_sum': weighted_sum,
            'total_weight': total_weight,
            'decision': decision,
            'claims': claim_details
        }
    
    def generate_report(self, paper_id: str, claims: List[Dict], 
                       verifications: Dict[str, Dict], weights: Dict[str, Dict]) -> str:
        """
        生成最终的 Meta-Review 报告
        
        Args:
            paper_id: 论文 ID
            claims: 所有观点列表
            verifications: 验证结果字典
            weights: 权重字典
            
        Returns:
            报告文本（英文）
        """
        # 过滤错误观点
        filtered_claims = self.filter_false_claims(claims, verifications)
        
        # 对每个主题进行加权投票
        topic_results = []
        for topic in self.topics:
            result = self.weighted_voting(topic, filtered_claims, weights)
            topic_results.append(result)
        
        # 生成报告
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append(f"Meta-Review Report for Paper: {paper_id}")
        report_lines.append("=" * 70)
        report_lines.append("")
        report_lines.append("This report is generated using the E-V-W Evaluation Stack.")
        report_lines.append("The evaluation process includes:")
        report_lines.append("  1. Structure Extraction: Claims extracted from reviews")
        report_lines.append("  2. Fact Verification: Claims verified against paper content")
        report_lines.append("  3. Bias Calculation: Reviewer credibility weights calculated")
        report_lines.append("  4. Meta-Review Synthesis: Weighted voting on topics")
        report_lines.append("")
        report_lines.append("-" * 70)
        report_lines.append("REVIEWER CREDIBILITY WEIGHTS")
        report_lines.append("-" * 70)
        report_lines.append("")
        
        # 显示权重
        sorted_weights = sorted(weights.items(), key=lambda x: x[1]['weight'], reverse=True)
        for reviewer_id, data in sorted_weights:
            report_lines.append(f"{reviewer_id}:")
            report_lines.append(f"  Weight: {data['weight']:.3f}")
            report_lines.append(f"  Hollowness: {data['hollowness']:.3f} "
                              f"({data['num_claims'] - data['num_claims_with_evidence']}/{data['num_claims']} claims without evidence)")
            report_lines.append(f"  Hallucination: {data['hallucination']:.3f} "
                              f"({data['num_false_claims']}/{data['num_claims_with_evidence']} false claims)")
            report_lines.append("")
        
        report_lines.append("-" * 70)
        report_lines.append("TOPIC-BASED EVALUATION")
        report_lines.append("-" * 70)
        report_lines.append("")
        
        # 显示每个主题的结果
        for result in topic_results:
            topic = result['topic']
            score = result['score']
            decision = result['decision']
            num_claims = result['num_claims']
            
            report_lines.append(f"Topic: {topic}")
            report_lines.append(f"  Score: {score:.3f}")
            report_lines.append(f"  Decision: {decision}")
            report_lines.append(f"  Number of claims: {num_claims}")
            
            if result['claims']:
                report_lines.append("  Key claims:")
                for claim_detail in result['claims'][:3]:  # 只显示前3个
                    sentiment = claim_detail['sentiment']
                    contribution = claim_detail['contribution']
                    report_lines.append(f"    - [{claim_detail['reviewer_id']}] {sentiment}: "
                                      f"{claim_detail['statement'][:80]}... "
                                      f"(contribution: {contribution:+.3f})")
            
            report_lines.append("")
        
        # 总体评估
        report_lines.append("-" * 70)
        report_lines.append("OVERALL ASSESSMENT")
        report_lines.append("-" * 70)
        report_lines.append("")
        
        # 计算平均分数
        valid_scores = [r['score'] for r in topic_results if r['num_claims'] > 0]
        if valid_scores:
            avg_score = sum(valid_scores) / len(valid_scores)
            report_lines.append(f"Average Topic Score: {avg_score:.3f}")
            
            # 统计决策
            decisions = [r['decision'] for r in topic_results if r['num_claims'] > 0]
            accept_count = decisions.count('Accept')
            reject_count = decisions.count('Reject')
            neutral_count = decisions.count('Neutral')
            
            report_lines.append(f"Topic Decisions: Accept={accept_count}, Reject={reject_count}, Neutral={neutral_count}")
            
            # 总体建议
            if avg_score >= self.accept_threshold:
                overall_decision = "ACCEPT"
            elif avg_score <= -self.accept_threshold:
                overall_decision = "REJECT"
            else:
                overall_decision = "NEUTRAL / REVISE"
            
            report_lines.append(f"Overall Recommendation: {overall_decision}")
        
        report_lines.append("")
        report_lines.append("=" * 70)
        report_lines.append("End of Report")
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)

