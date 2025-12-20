"""
Run Step 4: Meta-Review Synthesis
Generate final meta-review report
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
    print("Step 4: Meta-Review Synthesis (合成决策层)")
    print("=" * 70)
    print()
    
    # Initialize pipeline
    try:
        pipeline = EVWPipeline()
        print("[INFO] Pipeline initialized successfully")
        print(f"[INFO] Accept threshold: {pipeline.synthesis_agent.accept_threshold}")
        print(f"[INFO] Topics: {', '.join(pipeline.synthesis_agent.topics)}")
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
        report = pipeline.step4_synthesis(PAPER_ID)
        
        if report:
            print(f"\n[Summary] Report generated successfully")
            print(f"[INFO] Report saved to: data/results/synthesis/{PAPER_ID}_report.md")
            print(f"\n[Preview] First 500 characters of the report:")
            print("-" * 70)
            print(report[:500])
            print("...")
            print("-" * 70)
        else:
            print("[WARNING] No report generated. Check if previous steps were completed.")
        
    except Exception as e:
        print(f"[ERROR] Error processing paper {PAPER_ID}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

