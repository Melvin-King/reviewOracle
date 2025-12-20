"""
简单测试 Section 识别功能（不需要LLM）
"""

import sys
import io
from pathlib import Path

# 设置UTF-8编码输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.verification_agent import VerificationAgent
from src.utils.rag import SimpleRAG

def test_section_identification_logic():
    """测试section识别逻辑（不需要LLM）"""
    print("=" * 70)
    print("测试 Section 识别逻辑")
    print("=" * 70)
    print()
    
    # 创建VerificationAgent（不实际使用LLM）
    # 我们需要一个dummy LLMClient，但只测试section识别逻辑
    class DummyLLMClient:
        def call(self, *args, **kwargs):
            return '{"verification_result": "True", "verification_reason": "test", "confidence": 0.5}'
    
    dummy_llm = DummyLLMClient()
    rag = SimpleRAG()
    agent = VerificationAgent(dummy_llm, rag)
    
    # 模拟可用的sections
    available_sections = [
        "Introduction",
        "Related Work", 
        "Methodology",
        "Method",
        "Experiments",
        "Empirical Results",
        "Results",
        "Discussion",
        "Conclusion"
    ]
    
    # 测试claims
    test_cases = [
        {
            "id": "TEST-1",
            "topic": "Experiments",
            "statement": "The experiments are weak and lack comprehensive evaluation",
            "substantiation_content": "The evaluation metrics are not comprehensive enough"
        },
        {
            "id": "TEST-2", 
            "topic": "Methodology",
            "statement": "The method is novel and innovative",
            "substantiation_content": "The proposed algorithm uses a different approach"
        },
        {
            "id": "TEST-3",
            "topic": "Results",
            "statement": "The results show significant improvement",
            "substantiation_content": "Performance increased by 10% compared to baseline"
        },
        {
            "id": "TEST-4",
            "topic": "Novelty",
            "statement": "The approach is not novel",
            "substantiation_content": "Similar methods exist in previous work"
        }
    ]
    
    print("测试 Section 识别结果：\n")
    for i, claim in enumerate(test_cases, 1):
        identified = agent.identify_relevant_section(claim, available_sections)
        print(f"测试 {i}:")
        print(f"  Claim ID: {claim['id']}")
        print(f"  Topic: {claim['topic']}")
        print(f"  Statement: {claim['statement'][:60]}...")
        print(f"  -> 识别到的Section: {identified}")
        print()
    
    print("=" * 70)
    print("测试完成！")
    print("=" * 70)

if __name__ == "__main__":
    test_section_identification_logic()

