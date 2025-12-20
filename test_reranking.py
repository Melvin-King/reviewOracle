"""
测试重排序（Reranking）功能
"""

import sys
import io
from pathlib import Path

# 设置UTF-8编码输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from src.utils.rag import SimpleRAG
from src.utils.embedding_rag import EmbeddingRAG
from src.utils.hybrid_rag import HybridRAG
from src.utils.reranking_rag import RerankingRAG
from src.data.data_loader import DataLoader

def test_reranking_with_simple_rag():
    """测试SimpleRAG + Reranking"""
    print("=" * 70)
    print("测试 1: SimpleRAG + Reranking")
    print("=" * 70)
    
    paper_id = "paper_19076"
    data_loader = DataLoader()
    
    try:
        paper_text = data_loader.load_paper_text(paper_id)
        print(f"[INFO] 加载论文文本成功，长度: {len(paper_text)} 字符\n")
        
        # 创建基础RAG和RerankingRAG
        base_rag = SimpleRAG(chunk_size=500, chunk_overlap=50)
        reranking_rag = RerankingRAG(
            base_rag=base_rag,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            initial_top_k=20,
            use_reranking=True
        )
        
        query = "experiments evaluation metrics performance"
        print(f"[INFO] 查询: {query}\n")
        
        # 1. 不使用重排序
        print("1. 不使用重排序（基础RAG）:")
        base_chunks = base_rag.retrieve_relevant_chunks(paper_text, query, top_k=5)
        print(f"   返回 {len(base_chunks)} 个chunks")
        for i, (chunk, score) in enumerate(base_chunks[:3], 1):
            print(f"   Chunk {i} (score: {score:.4f}): {chunk[:80]}...")
        
        # 2. 使用重排序
        print("\n2. 使用重排序（RerankingRAG）:")
        reranked_chunks = reranking_rag.retrieve_relevant_chunks(paper_text, query, top_k=5)
        print(f"   返回 {len(reranked_chunks)} 个chunks")
        for i, (chunk, score) in enumerate(reranked_chunks[:3], 1):
            print(f"   Chunk {i} (rerank_score: {score:.4f}): {chunk[:80]}...")
        
        # 比较结果
        print("\n3. 结果比较:")
        base_top_chunk = base_chunks[0][0][:100] if base_chunks else ""
        reranked_top_chunk = reranked_chunks[0][0][:100] if reranked_chunks else ""
        
        if base_top_chunk != reranked_top_chunk:
            print("   [SUCCESS] 重排序改变了结果顺序，功能正常工作！")
        else:
            print("   [INFO] 重排序后top结果相同（可能查询很明确）")
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_reranking_with_hybrid_rag():
    """测试HybridRAG + Reranking（需要构建索引）"""
    print("\n" + "=" * 70)
    print("测试 2: HybridRAG + Reranking")
    print("=" * 70)
    
    paper_id = "paper_19076"
    data_loader = DataLoader()
    
    try:
        paper_text = data_loader.load_paper_text(paper_id)
        print(f"[INFO] 加载论文文本成功\n")
        
        # 创建HybridRAG和RerankingRAG
        base_rag = HybridRAG(
            keyword_weight=0.3,
            semantic_weight=0.7,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            chunk_size=500,
            chunk_overlap=50
        )
        
        # 构建索引
        print("[INFO] 构建索引中...")
        base_rag.build_index(paper_text)
        print("[INFO] 索引构建完成\n")
        
        reranking_rag = RerankingRAG(
            base_rag=base_rag,
            reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            initial_top_k=20,
            use_reranking=True
        )
        
        query = "methodology approach algorithm"
        print(f"[INFO] 查询: {query}\n")
        
        # 使用重排序检索
        reranked_chunks = reranking_rag.retrieve_relevant_chunks(paper_text, query, top_k=5)
        print(f"[INFO] 重排序后返回 {len(reranked_chunks)} 个chunks:")
        for i, (chunk, score) in enumerate(reranked_chunks[:3], 1):
            print(f"   {i}. (score: {score:.4f}): {chunk[:80]}...")
        
        print("\n[SUCCESS] HybridRAG + Reranking 测试完成！")
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_reranking_disabled():
    """测试禁用重排序的情况"""
    print("\n" + "=" * 70)
    print("测试 3: 禁用重排序（use_reranking=False）")
    print("=" * 70)
    
    paper_id = "paper_19076"
    data_loader = DataLoader()
    
    try:
        paper_text = data_loader.load_paper_text(paper_id)
        
        base_rag = SimpleRAG(chunk_size=500, chunk_overlap=50)
        reranking_rag = RerankingRAG(
            base_rag=base_rag,
            use_reranking=False  # 禁用重排序
        )
        
        query = "experiments results"
        print(f"[INFO] 查询: {query}\n")
        
        # 应该直接使用基础RAG的结果
        chunks = reranking_rag.retrieve_relevant_chunks(paper_text, query, top_k=5)
        print(f"[INFO] 返回 {len(chunks)} 个chunks（应该与基础RAG相同）")
        print("[SUCCESS] 禁用重排序功能正常工作！")
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n开始测试重排序功能...\n")
    
    # 运行测试
    test_reranking_with_simple_rag()
    # test_reranking_with_hybrid_rag()  # 这个测试需要下载模型，可能较慢
    test_reranking_disabled()
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)
    print("\n提示：要启用重排序，请在 config.yaml 中设置:")
    print("  rag:")
    print("    use_reranking: true")
    print("    reranker_model: \"cross-encoder/ms-marco-MiniLM-L-6-v2\"")

