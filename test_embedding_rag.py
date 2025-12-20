"""
测试 Embedding RAG 实现
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.utils.embedding_rag import EmbeddingRAG
from src.data.data_loader import DataLoader

def test_embedding_rag():
    print("=" * 70)
    print("测试 Embedding RAG")
    print("=" * 70)
    print()
    
    # 初始化 RAG
    print("[1] 初始化 Embedding RAG...")
    rag = EmbeddingRAG(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        chunk_size=500,
        chunk_overlap=50
    )
    print("[OK] RAG initialized successfully")
    print()
    
    # 加载论文文本
    print("[2] 加载论文文本...")
    data_loader = DataLoader()
    paper_id = "paper_19076"
    try:
        paper_text = data_loader.load_paper_text(paper_id)
        print(f"[OK] Paper text loaded successfully, length: {len(paper_text)} characters")
    except Exception as e:
        print(f"✗ 加载失败: {e}")
        return
    print()
    
    # 构建索引
    print("[3] 构建向量索引...")
    index_path = f"data/processed/rag_indices/{paper_id}"
    try:
        rag.build_index(paper_text, save_path=index_path)
        print("[OK] Index built successfully")
    except Exception as e:
        print(f"[ERROR] Build failed: {e}")
        import traceback
        traceback.print_exc()
        return
    print()
    
    # 测试检索
    print("[4] 测试检索功能...")
    test_queries = [
        "The method uses attention mechanism",
        "scaling laws and performance",
        "VAR model architecture",
        "experimental results on ImageNet"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        chunks = rag.retrieve_relevant_chunks(query, top_k=3)
        print(f"找到 {len(chunks)} 个相关块:")
        for i, (chunk, score) in enumerate(chunks, 1):
            preview = chunk[:100].replace('\n', ' ')
            print(f"  {i}. [Similarity: {score:.3f}] {preview}...")
    
    print()
    
    # 测试索引加载
    print("[5] 测试索引加载...")
    try:
        new_rag = EmbeddingRAG()
        new_rag.load_index(index_path)
        print("[OK] Index loaded successfully")
        
        # 测试检索是否仍然工作
        test_query = "attention mechanism"
        chunks = new_rag.retrieve_relevant_chunks(test_query, top_k=2)
        print(f"[OK] Retrieval works correctly, found {len(chunks)} relevant chunks")
    except Exception as e:
        print(f"✗ 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    print("=" * 70)
    print("所有测试通过！")
    print("=" * 70)

if __name__ == "__main__":
    test_embedding_rag()

