"""
测试 Section 过滤的 RAG 功能
"""

import sys
import io
from pathlib import Path

# 设置UTF-8编码输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from src.data.pdf_parser import PDFParser
from src.agents.verification_agent import VerificationAgent
from src.utils.llm_client import LLMClient
from src.utils.rag import SimpleRAG
from src.data.data_loader import DataLoader

def test_section_extraction():
    """测试section提取功能"""
    print("=" * 70)
    print("测试 1: Section 提取")
    print("=" * 70)
    
    paper_id = "paper_19076"
    data_loader = DataLoader()
    
    try:
        paper_text = data_loader.load_paper_text(paper_id)
        print(f"[INFO] 加载论文文本成功，长度: {len(paper_text)} 字符")
        
        pdf_parser = PDFParser()
        sections = pdf_parser.extract_sections(paper_text)
        
        print(f"[INFO] 提取到 {len(sections)} 个sections:")
        for section_name in sections.keys():
            section_len = len(sections[section_name])
            print(f"  - {section_name[:50]} ({section_len} chars)")
        
        return sections, paper_text
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_section_identification():
    """测试section识别功能"""
    print("\n" + "=" * 70)
    print("测试 2: Section 识别")
    print("=" * 70)
    
    # 创建VerificationAgent（不实际使用LLM，只测试section识别逻辑）
    try:
        llm_client = LLMClient()
    except:
        print("[WARNING] LLMClient初始化失败，跳过需要LLM的测试")
        return
    
    rag = SimpleRAG()
    agent = VerificationAgent(llm_client, rag)
    
    # 测试claims
    test_claims = [
        {
            "id": "TEST-1",
            "topic": "Experiments",
            "statement": "The experiments are weak",
            "substantiation_content": "The evaluation metrics are not comprehensive"
        },
        {
            "id": "TEST-2",
            "topic": "Methodology",
            "statement": "The method is novel",
            "substantiation_content": "The proposed algorithm is different from previous work"
        },
        {
            "id": "TEST-3",
            "topic": "Results",
            "statement": "The results show improvement",
            "substantiation_content": "Performance increased by 10%"
        }
    ]
    
    sections, paper_text = test_section_extraction()
    if not sections:
        return
    
    available_sections = list(sections.keys())
    print(f"\n[INFO] 可用sections: {available_sections}\n")
    
    for claim in test_claims:
        identified_section = agent.identify_relevant_section(claim, available_sections)
        print(f"Claim: {claim['statement'][:60]}")
        print(f"  Topic: {claim['topic']}")
        print(f"  Identified Section: {identified_section}")
        print()

def test_section_filtered_rag():
    """测试带section过滤的RAG检索"""
    print("\n" + "=" * 70)
    print("测试 3: Section 过滤的 RAG 检索")
    print("=" * 70)
    
    paper_id = "paper_19076"
    data_loader = DataLoader()
    
    try:
        paper_text = data_loader.load_paper_text(paper_id)
        pdf_parser = PDFParser()
        sections = pdf_parser.extract_sections(paper_text)
        
        # 创建RAG
        rag = SimpleRAG()
        
        # 测试查询
        query = "experiments evaluation metrics performance"
        
        print(f"\n[INFO] 查询: {query}\n")
        
        # 1. 全文检索
        print("1. 全文检索（无section过滤）:")
        context_full = rag.get_context(paper_text, query, top_k=3)
        print(f"   Context length: {len(context_full)} chars")
        if context_full:
            preview = context_full[:200].replace('\n', ' ')
            print(f"   Preview: {preview}...\n")
        else:
            print("   (No context found)\n")
        
        # 2. 只在Experiments section中检索
        # 查找包含"Empirical"或"Experiment"的section
        target_section = None
        for section_name in sections.keys():
            section_lower = section_name.lower()
            if "empirical" in section_lower or ("experiment" in section_lower and len(section_name) < 100):
                target_section = section_name
                print(f"[INFO] Found target section: {section_name}")
                print(f"[INFO] Section content length: {len(sections[section_name])} chars")
                break
        
        if target_section and sections[target_section]:
            print(f"2. Section过滤检索 (只搜索 '{target_section}' section):")
            context_filtered = rag.get_context(
                paper_text, query, top_k=3,
                target_section=target_section,
                paper_sections=sections
            )
            print(f"   Context length: {len(context_filtered)} chars")
            if context_filtered:
                preview = context_filtered[:200].replace('\n', ' ')
                print(f"   Preview: {preview}...\n")
            else:
                print("   (No context found)\n")
            
            if len(context_filtered) < len(context_full):
                print("[SUCCESS] Section filter is working! Filtered context is shorter.")
            elif len(context_filtered) > 0:
                print("[INFO] Section filter may not be working, or section contains much content.")
            else:
                print("[WARNING] No context found in filtered section.")
        else:
            print("[WARNING] 未找到Experiments section，跳过section过滤测试")
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n开始测试 Section 过滤功能...\n")
    
    # 运行所有测试
    test_section_extraction()
    test_section_identification()
    test_section_filtered_rag()
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)

