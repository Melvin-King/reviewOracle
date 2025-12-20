"""
Step 1: Structure Extraction Agent (结构化提取层)
从 Review 中提取原子观点并分类证据类型
"""

import json
from typing import List, Dict
from ..utils.llm_client import LLMClient


class ExtractionAgent:
    """结构化提取 Agent"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        
        self.system_prompt = """你是一个专业的学术评审分析专家。你的任务是从论文评审中提取结构化的观点。

对于每个观点，你需要提取：
1. topic: 主题（如 Novelty, Experiments, Writing, Significance, Reproducibility）
2. sentiment: 情感（Positive, Negative, Neutral）
3. statement: 观点陈述
4. substantiation_type: 证据类型
   - Specific_Citation: 有具体引用或明确证据
   - Vague: 模糊的、不具体的证据
   - None: 没有任何证据支撑
5. substantiation_content: 证据内容（如果有）

输出格式必须是有效的 JSON 数组。"""
    
    def extract_claims(self, review_text: str, reviewer_id: str = "R1") -> List[Dict]:
        """
        从 Review 文本中提取原子观点
        
        Args:
            review_text: Review 文本
            reviewer_id: Reviewer ID
            
        Returns:
            观点列表，每个包含 id, topic, sentiment, statement, 
            substantiation_type, substantiation_content
        """
        prompt = f"""请从以下评审文本中提取所有原子观点：

评审文本：
{review_text}

请按照要求提取观点，并以 JSON 数组格式输出。每个观点的 id 格式为 {reviewer_id}-C{{序号}}。"""
        
        response = self.llm.call(prompt, self.system_prompt)
        
        # 解析 JSON 响应
        try:
            # 尝试提取 JSON（可能包含 markdown 代码块）
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            claims = json.loads(json_str)
            
            # 确保每个 claim 都有完整的字段
            for i, claim in enumerate(claims):
                if 'id' not in claim:
                    claim['id'] = f"{reviewer_id}-C{i+1}"
                if 'substantiation_type' not in claim:
                    claim['substantiation_type'] = 'None'
                if 'substantiation_content' not in claim:
                    claim['substantiation_content'] = None
            
            return claims
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 解析失败: {e}")
            print(f"[DEBUG] LLM 响应: {response}")
            return []
    
    def process_reviews(self, reviews: List[Dict]) -> List[Dict]:
        """
        处理多个 reviews，提取所有观点
        
        Args:
            reviews: Review 列表，每个包含 reviewer_id 和 content
            
        Returns:
            所有观点的列表
        """
        all_claims = []
        
        for idx, review in enumerate(reviews):
            # 使用 review 索引生成 reviewer_id，而不是 all_claims 长度
            reviewer_id = review.get('reviewer_id', f"R{idx+1}")
            review_text = review.get('content', review.get('text', ''))
            
            if not review_text:
                print(f"[WARNING] Review {reviewer_id} 没有内容，跳过")
                continue
            
            claims = self.extract_claims(review_text, reviewer_id)
            all_claims.extend(claims)
        
        return all_claims

