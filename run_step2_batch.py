"""
批量运行 Step 2: Fact Verification Agent
对所有paper进行事实验证
"""

import sys
import io
from pathlib import Path

# 设置UTF-8编码输出（Windows兼容）
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import EVWPipeline

# 所有paper ID
PAPER_IDS = ["paper_19076", "paper_19094", "paper_21497"]

def main():
    print("=" * 70)
    print("Step 2: Fact Verification Agent (事实验证层) - 批量处理")
    print("=" * 70)
    print()
    
    # Initialize pipeline
    try:
        pipeline = EVWPipeline()
        print("[INFO] Pipeline initialized successfully")
        print(f"[INFO] Using LLM: {pipeline.llm_client.provider} / {pipeline.llm_client.model}")
        print(f"[INFO] RAG method: {type(pipeline.rag).__name__}")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to initialize pipeline: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Process each paper
    total_verified = 0
    total_true = 0
    total_false = 0
    total_partial = 0
    
    for i, paper_id in enumerate(PAPER_IDS, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(PAPER_IDS)}] Processing paper: {paper_id}")
        print(f"{'='*70}\n")
        
        try:
            verifications = pipeline.step2_verification(paper_id)
            
            if verifications:
                print(f"\n[Summary] Verification Results for {paper_id}:")
                print(f"  - Total verified claims: {len(verifications)}")
                
                # Statistics
                results = [v['verification_result'] for v in verifications.values()]
                true_count = results.count('True')
                false_count = results.count('False')
                partial_count = results.count('Partially_True')
                
                print(f"  - True: {true_count}")
                print(f"  - False: {false_count}")
                print(f"  - Partially_True: {partial_count}")
                
                # Average confidence
                avg_confidence = sum(v['confidence'] for v in verifications.values()) / len(verifications)
                print(f"  - Average confidence: {avg_confidence:.2f}")
                
                # Accumulate totals
                total_verified += len(verifications)
                total_true += true_count
                total_false += false_count
                total_partial += partial_count
            else:
                print(f"[WARNING] No verifications returned for {paper_id}")
            
            print(f"\n[INFO] Results saved to: data/results/verifications/{paper_id}_verified.json")
            
        except Exception as e:
            print(f"[ERROR] Error processing paper {paper_id}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Final summary
    print(f"\n{'='*70}")
    print("Final Summary (All Papers)")
    print(f"{'='*70}")
    print(f"  - Total papers processed: {len(PAPER_IDS)}")
    print(f"  - Total verified claims: {total_verified}")
    print(f"  - True: {total_true}")
    print(f"  - False: {total_false}")
    print(f"  - Partially_True: {total_partial}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()

