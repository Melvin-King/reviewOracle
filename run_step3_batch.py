"""
批量运行 Step 3: Weighting Agent
对所有paper进行权重计算
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
    print("Step 3: Weighting Agent (权重计算层) - 批量处理")
    print("=" * 70)
    print()
    
    # Initialize pipeline
    try:
        pipeline = EVWPipeline()
        print("[INFO] Pipeline initialized successfully")
        print(f"[INFO] Using LLM: {pipeline.llm_client.provider} / {pipeline.llm_client.model}")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to initialize pipeline: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Process each paper
    for i, paper_id in enumerate(PAPER_IDS, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(PAPER_IDS)}] Processing paper: {paper_id}")
        print(f"{'='*70}\n")
        
        try:
            weights = pipeline.step3_weighting(paper_id)
            
            if weights:
                print(f"\n[Summary] Weighting Results for {paper_id}:")
                print(f"  - Total reviewers: {len(weights)}")
                
                # Show weights for each reviewer
                for reviewer_id, weight_data in weights.items():
                    weight = weight_data.get('weight', 0)
                    hollowness = weight_data.get('hollowness', 0)
                    hallucination = weight_data.get('hallucination', 0)
                    print(f"  - {reviewer_id}: weight={weight:.3f}, hollowness={hollowness:.3f}, hallucination={hallucination:.3f}")
            else:
                print(f"[WARNING] No weights returned for {paper_id}")
            
            print(f"\n[INFO] Results saved to: data/results/weights/{paper_id}_weights.json")
            
        except Exception as e:
            print(f"[ERROR] Error processing paper {paper_id}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*70}")
    print("Step 3 批量处理完成！")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()

