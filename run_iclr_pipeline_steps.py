"""
Run Steps 1, 2, 3 of the E-V-W pipeline for ICLR 2024 papers
All outputs are in English
"""

import sys
import io
from pathlib import Path
import json

# Set UTF-8 encoding for Windows
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pipeline import EVWPipeline


def get_iclr_papers():
    """Get ICLR 2024 paper IDs"""
    accepted_dir = Path("data/raw/iclr2024/papers/accepted")
    rejected_dir = Path("data/raw/iclr2024/papers/rejected")
    
    accepted_papers = []
    rejected_papers = []
    
    if accepted_dir.exists():
        accepted_papers = [f.stem for f in accepted_dir.glob("*.pdf")]
    
    if rejected_dir.exists():
        rejected_papers = [f.stem for f in rejected_dir.glob("*.pdf")]
    
    return accepted_papers[:5], rejected_papers[:5]


def setup_iclr_paper_paths(paper_id, paper_type):
    """Setup symlinks or copy files to expected paths for ICLR papers"""
    from pathlib import Path
    import shutil
    
    base_path = Path("data")
    
    # Source paths
    if paper_type == "Accepted":
        src_pdf = Path(f"data/raw/iclr2024/papers/accepted/{paper_id}.pdf")
    else:
        src_pdf = Path(f"data/raw/iclr2024/papers/rejected/{paper_id}.pdf")
    
    src_reviews = Path(f"data/raw/iclr2024/reviews/{paper_id}_reviews.json")
    
    # Target paths (expected by DataLoader)
    target_pdf = base_path / "raw" / "papers" / f"{paper_id}.pdf"
    target_reviews = base_path / "raw" / "reviews" / f"{paper_id}_reviews.json"
    
    # Create symlinks or copy files
    if src_pdf.exists() and not target_pdf.exists():
        target_pdf.parent.mkdir(parents=True, exist_ok=True)
        try:
            target_pdf.symlink_to(src_pdf.absolute())
        except:
            shutil.copy2(src_pdf, target_pdf)
    
    if src_reviews.exists() and not target_reviews.exists():
        target_reviews.parent.mkdir(parents=True, exist_ok=True)
        try:
            target_reviews.symlink_to(src_reviews.absolute())
        except:
            shutil.copy2(src_reviews, target_reviews)


def run_steps_for_paper(pipeline, paper_id, paper_type):
    """Run steps 1, 2, 3 for a single paper"""
    print(f"\n{'='*70}")
    print(f"Processing {paper_type.upper()} Paper: {paper_id}")
    print(f"{'='*70}\n")
    
    results = {}
    
    try:
        # Step 1: Extraction
        print(f"[Step 1] Extracting claims from reviews...")
        claims = pipeline.step1_extraction(paper_id)
        results['step1'] = {
            'success': True,
            'num_claims': len(claims) if claims else 0
        }
        print(f"[Step 1] Completed: Extracted {len(claims) if claims else 0} claims\n")
        
    except Exception as e:
        print(f"[Step 1] Error: {e}\n")
        results['step1'] = {
            'success': False,
            'error': str(e)
        }
        return results
    
    try:
        # Step 2: Verification
        print(f"[Step 2] Verifying claims against paper content...")
        verifications = pipeline.step2_verification(paper_id)
        if verifications:
            true_count = sum(1 for v in verifications.values() if v.get('is_supported') == True)
            false_count = sum(1 for v in verifications.values() if v.get('is_supported') == False)
            results['step2'] = {
                'success': True,
                'num_verified': len(verifications),
                'true_count': true_count,
                'false_count': false_count
            }
            print(f"[Step 2] Completed: Verified {len(verifications)} claims ({true_count} True, {false_count} False)\n")
        else:
            results['step2'] = {
                'success': False,
                'error': 'No verifications returned'
            }
            print(f"[Step 2] Warning: No verifications returned\n")
            
    except Exception as e:
        print(f"[Step 2] Error: {e}\n")
        results['step2'] = {
            'success': False,
            'error': str(e)
        }
        return results
    
    try:
        # Step 3: Weighting
        print(f"[Step 3] Calculating reviewer weights...")
        weights = pipeline.step3_weighting(paper_id)
        if weights:
            results['step3'] = {
                'success': True,
                'num_reviewers': len(weights),
                'weights': {k: v.get('weight', 0) for k, v in weights.items()}
            }
            print(f"[Step 3] Completed: Calculated weights for {len(weights)} reviewers\n")
        else:
            results['step3'] = {
                'success': False,
                'error': 'No weights returned'
            }
            print(f"[Step 3] Warning: No weights returned\n")
            
    except Exception as e:
        print(f"[Step 3] Error: {e}\n")
        results['step3'] = {
            'success': False,
            'error': str(e)
        }
    
    return results


def get_ground_truth_status(paper_id):
    """Get ground truth acceptance status from paper info"""
    info_path = Path(f"data/raw/iclr2024/papers/accepted/{paper_id}_info.json")
    if info_path.exists():
        return "Accepted"
    
    info_path = Path(f"data/raw/iclr2024/papers/rejected/{paper_id}_info.json")
    if info_path.exists():
        return "Rejected"
    
    return "Unknown"


def calculate_statistics(all_results):
    """Calculate statistics from all results"""
    stats = {
        'total_papers': len(all_results),
        'accepted_papers': 0,
        'rejected_papers': 0,
        'step1_success': 0,
        'step2_success': 0,
        'step3_success': 0,
        'total_claims': 0,
        'total_verified': 0,
        'total_true': 0,
        'total_false': 0,
        'papers_by_status': {}
    }
    
    for paper_id, result in all_results.items():
        paper_type = result.get('paper_type', 'Unknown')
        if paper_type == 'Accepted':
            stats['accepted_papers'] += 1
        elif paper_type == 'Rejected':
            stats['rejected_papers'] += 1
        
        if result.get('step1', {}).get('success'):
            stats['step1_success'] += 1
            stats['total_claims'] += result['step1'].get('num_claims', 0)
        
        if result.get('step2', {}).get('success'):
            stats['step2_success'] += 1
            stats['total_verified'] += result['step2'].get('num_verified', 0)
            stats['total_true'] += result['step2'].get('true_count', 0)
            stats['total_false'] += result['step2'].get('false_count', 0)
        
        if result.get('step3', {}).get('success'):
            stats['step3_success'] += 1
    
    return stats


def main():
    """Main function"""
    print("="*70)
    print("ICLR 2024 Pipeline: Steps 1, 2, 3 Execution")
    print("="*70)
    print()
    
    # Initialize pipeline
    try:
        pipeline = EVWPipeline(config_path="config.yaml")
        print("[INFO] Pipeline initialized successfully\n")
    except Exception as e:
        print(f"[ERROR] Failed to initialize pipeline: {e}")
        return
    
    # Get paper lists
    accepted_papers, rejected_papers = get_iclr_papers()
    
    print(f"[INFO] Found {len(accepted_papers)} accepted papers and {len(rejected_papers)} rejected papers")
    print(f"[INFO] Processing {min(5, len(accepted_papers))} accepted and {min(5, len(rejected_papers))} rejected papers\n")
    
    all_results = {}
    
    # Process accepted papers
    for paper_id in accepted_papers[:5]:
        setup_iclr_paper_paths(paper_id, "Accepted")
        result = run_steps_for_paper(pipeline, paper_id, "Accepted")
        result['paper_type'] = 'Accepted'
        result['ground_truth'] = 'Accepted'
        all_results[paper_id] = result
    
    # Process rejected papers
    for paper_id in rejected_papers[:5]:
        setup_iclr_paper_paths(paper_id, "Rejected")
        result = run_steps_for_paper(pipeline, paper_id, "Rejected")
        result['paper_type'] = 'Rejected'
        result['ground_truth'] = 'Rejected'
        all_results[paper_id] = result
    
    # Calculate statistics
    stats = calculate_statistics(all_results)
    
    # Print summary
    print("\n" + "="*70)
    print("EXECUTION SUMMARY")
    print("="*70)
    print(f"\nTotal Papers Processed: {stats['total_papers']}")
    print(f"  - Accepted: {stats['accepted_papers']}")
    print(f"  - Rejected: {stats['rejected_papers']}")
    
    print(f"\nStep 1 (Extraction):")
    print(f"  - Success: {stats['step1_success']}/{stats['total_papers']}")
    print(f"  - Total Claims Extracted: {stats['total_claims']}")
    
    print(f"\nStep 2 (Verification):")
    print(f"  - Success: {stats['step2_success']}/{stats['total_papers']}")
    print(f"  - Total Claims Verified: {stats['total_verified']}")
    print(f"  - True Claims: {stats['total_true']}")
    print(f"  - False Claims: {stats['total_false']}")
    if stats['total_verified'] > 0:
        print(f"  - True Rate: {stats['total_true']/stats['total_verified']*100:.2f}%")
    
    print(f"\nStep 3 (Weighting):")
    print(f"  - Success: {stats['step3_success']}/{stats['total_papers']}")
    
    # Save results
    results_path = Path("data/results/iclr2024_pipeline_results.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    output = {
        'statistics': stats,
        'detailed_results': all_results
    }
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n[INFO] Results saved to: {results_path}")
    print("="*70)


if __name__ == "__main__":
    main()

