"""
批量运行 Step 4: Synthesis Agent
对所有paper生成最终报告
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
    print("Step 4: Synthesis Agent (合成决策层) - 批量处理")
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
            report_path = pipeline.step4_synthesis(paper_id)
            
            # Check if report was generated (report_path might be None, but file might exist)
            expected_path = Path(f"data/results/synthesis/{paper_id}_report.md")
            if expected_path.exists():
                print(f"\n[SUCCESS] Report generated for {paper_id}")
                print(f"[INFO] Report saved to: {expected_path}")
                
                # Show file size
                file_size = expected_path.stat().st_size
                print(f"[INFO] Report size: {file_size:,} bytes")
                
                # Show first few lines
                with open(expected_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:10]
                    print(f"\n[Preview] First 10 lines:")
                    print("-" * 70)
                    for line in lines:
                        print(line.rstrip())
                    print("-" * 70)
            else:
                print(f"[WARNING] Report file not found for {paper_id}")
            
        except Exception as e:
            print(f"[ERROR] Error processing paper {paper_id}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*70}")
    print("Step 4 批量处理完成！")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()

