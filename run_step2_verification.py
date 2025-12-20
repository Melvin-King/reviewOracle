"""
Run Step 2: Fact Verification Agent
Verify claims against paper content
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
    print("Step 2: Fact Verification Agent (事实验证层)")
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
    
    # Process the paper
    print(f"\n{'='*70}")
    print(f"Processing paper: {PAPER_ID}")
    print(f"{'='*70}\n")
    
    try:
        verifications = pipeline.step2_verification(PAPER_ID)
        
        if verifications:
            print(f"\n[Summary] Verification Results:")
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
        else:
            print("[WARNING] No verifications returned. Check if Step 1 was completed.")
        
        print(f"\n[INFO] Results saved to: data/results/verifications/{PAPER_ID}_verified.json")
        
    except Exception as e:
        print(f"[ERROR] Error processing paper {PAPER_ID}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


