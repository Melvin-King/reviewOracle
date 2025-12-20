"""
运行 Step 1: Structure Extraction Agent
从所有论文的 reviews 中提取结构化观点
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import EVWPipeline

# 需要处理的论文列表
PAPERS = [
    "paper_19076",
    "paper_19094", 
    "paper_21497"
]

def main():
    print("=" * 70)
    print("Step 1: Structure Extraction Agent (结构化提取层)")
    print("=" * 70)
    print()
    
    # 初始化 pipeline
    try:
        pipeline = EVWPipeline()
        print("[INFO] Pipeline 初始化成功")
        print(f"[INFO] 使用 LLM: {pipeline.llm_client.provider} / {pipeline.llm_client.model}")
        print()
    except Exception as e:
        print(f"[ERROR] Pipeline 初始化失败: {e}")
        return
    
    # 处理每篇论文
    all_results = {}
    
    for i, paper_id in enumerate(PAPERS, 1):
        print(f"\n{'='*70}")
        print(f"处理论文 {i}/{len(PAPERS)}: {paper_id}")
        print(f"{'='*70}\n")
        
        try:
            claims = pipeline.step1_extraction(paper_id)
            all_results[paper_id] = {
                'num_claims': len(claims),
                'claims': claims
            }
            
            # 显示统计信息
            if claims:
                # 统计各类型的证据
                substantiation_types = {}
                topics = {}
                sentiments = {}
                
                for claim in claims:
                    st_type = claim.get('substantiation_type', 'Unknown')
                    substantiation_types[st_type] = substantiation_types.get(st_type, 0) + 1
                    
                    topic = claim.get('topic', 'Unknown')
                    topics[topic] = topics.get(topic, 0) + 1
                    
                    sentiment = claim.get('sentiment', 'Unknown')
                    sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
                
                print(f"\n[统计] 提取结果:")
                print(f"  - 总观点数: {len(claims)}")
                print(f"  - 证据类型分布:")
                for st_type, count in substantiation_types.items():
                    print(f"    * {st_type}: {count}")
                print(f"  - 主题分布:")
                for topic, count in sorted(topics.items(), key=lambda x: -x[1])[:5]:
                    print(f"    * {topic}: {count}")
                print(f"  - 情感分布:")
                for sentiment, count in sentiments.items():
                    print(f"    * {sentiment}: {count}")
            
        except Exception as e:
            print(f"[ERROR] 处理论文 {paper_id} 时出错: {e}")
            import traceback
            traceback.print_exc()
            all_results[paper_id] = {'error': str(e)}
    
    # 总结
    print(f"\n{'='*70}")
    print("Step 1 完成总结")
    print(f"{'='*70}\n")
    
    total_claims = sum(r.get('num_claims', 0) for r in all_results.values())
    print(f"总共处理了 {len(PAPERS)} 篇论文")
    print(f"总共提取了 {total_claims} 个观点")
    
    for paper_id, result in all_results.items():
        if 'error' in result:
            print(f"  - {paper_id}: 失败 ({result['error']})")
        else:
            print(f"  - {paper_id}: {result['num_claims']} 个观点")
    
    print("\n所有结果已保存到: data/processed/extracted/")

if __name__ == "__main__":
    main()

