"""
Run Step 3: Bias Calculation & Weighting
Calculate reviewer credibility weights
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import EVWPipeline

# Paper to process (one at a time)
PAPER_ID = "paper_19076"  # Change this to process different papers

def main():
    print("=" * 70)
    print("Step 3: Bias Calculation & Weighting (偏差计算与加权层)")
    print("=" * 70)
    print()
    
    # Initialize pipeline
    try:
        pipeline = EVWPipeline()
        print("[INFO] Pipeline initialized successfully")
        print(f"[INFO] Weighting parameters: alpha={pipeline.weighting_agent.alpha}, beta={pipeline.weighting_agent.beta}")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to initialize pipeline: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Process the paper
    print(f"\n{'='*70}")
    print(f"Processing paper: {PAPER_ID}")
    print(f"{'='*70}\n")
    
    try:
        weights = pipeline.step3_weighting(PAPER_ID)
        
        if weights:
            print(f"\n[Summary] Weight Calculation Results:")
            print(f"  - Total reviewers: {len(weights)}")
            
            # Statistics
            avg_weight = sum(w['weight'] for w in weights.values()) / len(weights)
            min_weight = min(w['weight'] for w in weights.values())
            max_weight = max(w['weight'] for w in weights.values())
            
            print(f"  - Average weight: {avg_weight:.3f}")
            print(f"  - Min weight: {min_weight:.3f}")
            print(f"  - Max weight: {max_weight:.3f}")
            
            # Show weight ranking
            print(f"\n[Ranking] Reviewers by credibility weight:")
            sorted_reviewers = sorted(weights.items(), key=lambda x: x[1]['weight'], reverse=True)
            for rank, (reviewer_id, data) in enumerate(sorted_reviewers, 1):
                print(f"  {rank}. {reviewer_id}: {data['weight']:.3f} "
                      f"(Hollowness: {data['hollowness']:.3f}, "
                      f"Hallucination: {data['hallucination']:.3f})")
        else:
            print("[WARNING] No weights calculated. Check if Step 1 and Step 2 were completed.")
        
        print(f"\n[INFO] Results saved to: data/results/weights/{PAPER_ID}_weights.json")
        
    except Exception as e:
        print(f"[ERROR] Error processing paper {PAPER_ID}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

