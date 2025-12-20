"""
测试重排序功能在完整pipeline中的集成
"""

import sys
import io
from pathlib import Path

# 设置UTF-8编码输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from src.utils.rag import SimpleRAG
from src.utils.reranking_rag import RerankingRAG
from src.data.data_loader import DataLoader

def test_reranking_comparison():
    """对比重排序前后的检索结果"""
    print("=" * 70)
    print("重排序效果对比测试")
    print("=" * 70)
    print()
    
    paper_id = "paper_19076"
    data_loader = DataLoader()
    
    try:
        paper_text = data_loader.load_paper_text(paper_id)
        print(f"[INFO] 加载论文文本成功，长度: {len(paper_text)} 字符\n")
        
        # 创建基础RAG
        base_rag = SimpleRAG(chunk_size=500, chunk_overlap=50)
        
        # 创建带重排序的RAG
        reranking_rag = RerankingRAG(
            base_rag=base_rag,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            initial_top_k=20,
            use_reranking=True
        )
        
        # 测试多个查询
        test_queries = [
            {
                "name": "实验相关查询",
                "query": "experiments evaluation metrics performance results"
            },
            {
                "name": "方法相关查询",
                "query": "methodology approach algorithm design"
            },
            {
                "name": "结果相关查询",
                "query": "results show improvement accuracy"
            }
        ]
        
        for test_case in test_queries:
            print(f"查询类型: {test_case['name']}")
            print(f"查询内容: {test_case['query']}\n")
            
            # 基础RAG结果
            base_results = base_rag.retrieve_relevant_chunks(paper_text, test_case['query'], top_k=5)
            
            # 重排序结果
            reranked_results = reranking_rag.retrieve_relevant_chunks(paper_text, test_case['query'], top_k=5)
            
            print("基础RAG Top 3:")
            for i, (chunk, score) in enumerate(base_results[:3], 1):
                preview = chunk[:60].replace('\n', ' ')
                print(f"  {i}. (score: {score:.4f}) {preview}...")
            
            print("\n重排序后 Top 3:")
            for i, (chunk, score) in enumerate(reranked_results[:3], 1):
                preview = chunk[:60].replace('\n', ' ')
                print(f"  {i}. (rerank_score: {score:.4f}) {preview}...")
            
            # 检查是否改变了顺序
            base_top = base_results[0][0][:50] if base_results else ""
            reranked_top = reranked_results[0][0][:50] if reranked_results else ""
            
            if base_top != reranked_top:
                print("\n  [SUCCESS] ✓ 重排序改变了top结果")
            else:
                print("\n  [INFO] - 重排序后top结果相同（可能查询很明确）")
            
            print("\n" + "-" * 70 + "\n")
        
        print("[SUCCESS] 所有测试完成！")
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_reranking_performance():
    """测试重排序的性能影响"""
    print("=" * 70)
    print("重排序性能测试")
    print("=" * 70)
    print()
    
    import time
    
    paper_id = "paper_19076"
    data_loader = DataLoader()
    
    try:
        paper_text = data_loader.load_paper_text(paper_id)
        
        base_rag = SimpleRAG(chunk_size=500, chunk_overlap=50)
        reranking_rag = RerankingRAG(
            base_rag=base_rag,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            initial_top_k=20,
            use_reranking=True
        )
        
        query = "experiments evaluation metrics"
        
        # 测试基础RAG性能
        print("测试基础RAG检索时间...")
        start = time.time()
        for _ in range(5):
            base_rag.retrieve_relevant_chunks(paper_text, query, top_k=5)
        base_time = (time.time() - start) / 5
        print(f"  平均时间: {base_time:.3f} 秒\n")
        
        # 测试重排序RAG性能
        print("测试重排序RAG检索时间...")
        start = time.time()
        for _ in range(5):
            reranking_rag.retrieve_relevant_chunks(paper_text, query, top_k=5)
        rerank_time = (time.time() - start) / 5
        print(f"  平均时间: {rerank_time:.3f} 秒\n")
        
        overhead = rerank_time - base_time
        overhead_percent = (overhead / base_time) * 100 if base_time > 0 else 0
        
        print(f"性能对比:")
        print(f"  基础RAG: {base_time:.3f} 秒")
        print(f"  重排序RAG: {rerank_time:.3f} 秒")
        print(f"  额外开销: {overhead:.3f} 秒 ({overhead_percent:.1f}%)")
        
        if overhead < 1.0:
            print(f"\n[SUCCESS] ✓ 重排序开销在可接受范围内（< 1秒）")
        else:
            print(f"\n[WARNING] 重排序开销较大，建议减少 initial_top_k")
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n开始测试重排序集成功能...\n")
    
    test_reranking_comparison()
    print("\n")
    test_reranking_performance()
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)

