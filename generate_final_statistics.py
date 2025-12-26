"""
Generate final statistics comparing pipeline results with ground truth
All outputs in English
"""

import sys
import io
import json
from pathlib import Path
from collections import defaultdict

# Set UTF-8 encoding for Windows
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass


def get_ground_truth_status(paper_id):
    """Get ground truth acceptance status"""
    accepted_path = Path(f"data/raw/iclr2024/papers/accepted/{paper_id}.pdf")
    rejected_path = Path(f"data/raw/iclr2024/papers/rejected/{paper_id}.pdf")
    
    if accepted_path.exists():
        return "Accepted"
    elif rejected_path.exists():
        return "Rejected"
    return "Unknown"


def load_all_results():
    """Load all pipeline results"""
    results = {}
    
    claims_dir = Path("data/processed/extracted")
    verifications_dir = Path("data/results/verifications")
    weights_dir = Path("data/results/weights")
    
    paper_ids = set()
    for claims_file in claims_dir.glob("*_claims.json"):
        paper_id = claims_file.stem.replace("_claims", "")
        paper_ids.add(paper_id)
    
    for paper_id in paper_ids:
        ground_truth = get_ground_truth_status(paper_id)
        if ground_truth == "Unknown":
            continue  # Skip non-ICLR papers
        
        result = {
            'paper_id': paper_id,
            'ground_truth': ground_truth,
            'step1': {},
            'step2': {},
            'step3': {}
        }
        
        # Step 1
        claims_file = claims_dir / f"{paper_id}_claims.json"
        if claims_file.exists():
            with open(claims_file, 'r', encoding='utf-8') as f:
                claims = json.load(f)
                result['step1'] = {
                    'num_claims': len(claims),
                    'claims': claims
                }
        
        # Step 2
        verifications_file = verifications_dir / f"{paper_id}_verified.json"
        if verifications_file.exists():
            with open(verifications_file, 'r', encoding='utf-8') as f:
                verifications = json.load(f)
                if isinstance(verifications, list):
                    verifications = {v['id']: v for v in verifications}
                
                true_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'True')
                false_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'False')
                partial_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'Partially_True')
                
                result['step2'] = {
                    'num_verified': len(verifications),
                    'true_count': true_count,
                    'false_count': false_count,
                    'partial_count': partial_count,
                    'verifications': verifications
                }
        
        # Step 3
        weights_file = weights_dir / f"{paper_id}_weights.json"
        if weights_file.exists():
            with open(weights_file, 'r', encoding='utf-8') as f:
                weights = json.load(f)
                result['step3'] = {
                    'num_reviewers': len(weights),
                    'weights': weights,
                    'avg_weight': sum(v.get('weight', 0) for v in weights.values()) / len(weights) if weights else 0
                }
        
        results[paper_id] = result
    
    return results


def calculate_comparison_statistics(results):
    """Calculate statistics comparing accepted vs rejected papers"""
    stats = {
        'accepted': {
            'count': 0,
            'total_claims': 0,
            'total_verified': 0,
            'total_true': 0,
            'total_false': 0,
            'total_partial': 0,
            'total_reviewers': 0,
            'avg_weight': [],
            'avg_claims_per_paper': 0,
            'avg_verified_per_paper': 0,
            'true_rate': 0,
            'false_rate': 0
        },
        'rejected': {
            'count': 0,
            'total_claims': 0,
            'total_verified': 0,
            'total_true': 0,
            'total_false': 0,
            'total_partial': 0,
            'total_reviewers': 0,
            'avg_weight': [],
            'avg_claims_per_paper': 0,
            'avg_verified_per_paper': 0,
            'true_rate': 0,
            'false_rate': 0
        }
    }
    
    for paper_id, result in results.items():
        ground_truth = result.get('ground_truth')
        if ground_truth not in ['Accepted', 'Rejected']:
            continue
        
        group = stats[ground_truth.lower()]
        group['count'] += 1
        
        # Step 1
        if result.get('step1'):
            num_claims = result['step1'].get('num_claims', 0)
            group['total_claims'] += num_claims
        
        # Step 2
        if result.get('step2'):
            num_verified = result['step2'].get('num_verified', 0)
            group['total_verified'] += num_verified
            group['total_true'] += result['step2'].get('true_count', 0)
            group['total_false'] += result['step2'].get('false_count', 0)
            group['total_partial'] += result['step2'].get('partial_count', 0)
        
        # Step 3
        if result.get('step3'):
            group['total_reviewers'] += result['step3'].get('num_reviewers', 0)
            avg_weight = result['step3'].get('avg_weight', 0)
            if avg_weight > 0:
                group['avg_weight'].append(avg_weight)
    
    # Calculate averages
    for status in ['accepted', 'rejected']:
        group = stats[status]
        if group['count'] > 0:
            group['avg_claims_per_paper'] = group['total_claims'] / group['count']
            group['avg_verified_per_paper'] = group['total_verified'] / group['count']
            if group['total_verified'] > 0:
                group['true_rate'] = group['total_true'] / group['total_verified']
                group['false_rate'] = group['total_false'] / group['total_verified']
            if group['avg_weight']:
                group['avg_weight'] = sum(group['avg_weight']) / len(group['avg_weight'])
            else:
                group['avg_weight'] = 0
    
    return stats


def print_comparison_report(results, comparison_stats):
    """Print comprehensive comparison report"""
    print("="*70)
    print("ICLR 2024 PIPELINE RESULTS: ACCEPTED vs REJECTED COMPARISON")
    print("="*70)
    print()
    
    # Overall summary
    print("1. OVERALL SUMMARY")
    print("-"*70)
    total_papers = comparison_stats['accepted']['count'] + comparison_stats['rejected']['count']
    print(f"Total Papers Analyzed: {total_papers}")
    print(f"  - Accepted Papers: {comparison_stats['accepted']['count']}")
    print(f"  - Rejected Papers: {comparison_stats['rejected']['count']}")
    print()
    
    # Step 1 comparison
    print("2. STEP 1: CLAIM EXTRACTION COMPARISON")
    print("-"*70)
    acc = comparison_stats['accepted']
    rej = comparison_stats['rejected']
    
    print(f"Accepted Papers:")
    print(f"  - Total Claims: {acc['total_claims']}")
    print(f"  - Average Claims per Paper: {acc['avg_claims_per_paper']:.1f}")
    print()
    print(f"Rejected Papers:")
    print(f"  - Total Claims: {rej['total_claims']}")
    print(f"  - Average Claims per Paper: {rej['avg_claims_per_paper']:.1f}")
    print()
    
    # Step 2 comparison
    print("3. STEP 2: FACT VERIFICATION COMPARISON")
    print("-"*70)
    print(f"Accepted Papers:")
    print(f"  - Total Verified: {acc['total_verified']}")
    print(f"  - Average Verified per Paper: {acc['avg_verified_per_paper']:.1f}")
    print(f"  - True: {acc['total_true']} ({acc['true_rate']*100:.1f}%)")
    print(f"  - False: {acc['total_false']} ({acc['false_rate']*100:.1f}%)")
    print(f"  - Partially True: {acc['total_partial']} ({acc['total_partial']/acc['total_verified']*100:.1f}%)" if acc['total_verified'] > 0 else "  - Partially True: 0")
    print()
    print(f"Rejected Papers:")
    print(f"  - Total Verified: {rej['total_verified']}")
    print(f"  - Average Verified per Paper: {rej['avg_verified_per_paper']:.1f}")
    print(f"  - True: {rej['total_true']} ({rej['true_rate']*100:.1f}%)")
    print(f"  - False: {rej['total_false']} ({rej['false_rate']*100:.1f}%)")
    print(f"  - Partially True: {rej['total_partial']} ({rej['total_partial']/rej['total_verified']*100:.1f}%)" if rej['total_verified'] > 0 else "  - Partially True: 0")
    print()
    
    # Step 3 comparison
    print("4. STEP 3: REVIEWER WEIGHTING COMPARISON")
    print("-"*70)
    print(f"Accepted Papers:")
    print(f"  - Total Reviewers: {acc['total_reviewers']}")
    print(f"  - Average Reviewers per Paper: {acc['total_reviewers']/acc['count']:.1f}" if acc['count'] > 0 else "  - Average Reviewers per Paper: N/A")
    print(f"  - Average Reviewer Weight: {acc['avg_weight']:.3f}")
    print()
    print(f"Rejected Papers:")
    print(f"  - Total Reviewers: {rej['total_reviewers']}")
    print(f"  - Average Reviewers per Paper: {rej['total_reviewers']/rej['count']:.1f}" if rej['count'] > 0 else "  - Average Reviewers per Paper: N/A")
    print(f"  - Average Reviewer Weight: {rej['avg_weight']:.3f}")
    print()
    
    # Key insights
    print("5. KEY INSIGHTS")
    print("-"*70)
    
    # Compare claim counts
    if acc['avg_claims_per_paper'] > rej['avg_claims_per_paper']:
        diff = acc['avg_claims_per_paper'] - rej['avg_claims_per_paper']
        print(f"• Accepted papers have {diff:.1f} more claims per paper on average")
    else:
        diff = rej['avg_claims_per_paper'] - acc['avg_claims_per_paper']
        print(f"• Rejected papers have {diff:.1f} more claims per paper on average")
    
    # Compare verification rates
    if acc['true_rate'] > rej['true_rate']:
        diff = (acc['true_rate'] - rej['true_rate']) * 100
        print(f"• Accepted papers have {diff:.1f}% higher true claim rate")
    else:
        diff = (rej['true_rate'] - acc['true_rate']) * 100
        print(f"• Rejected papers have {diff:.1f}% higher true claim rate")
    
    if acc['false_rate'] > rej['false_rate']:
        diff = (acc['false_rate'] - rej['false_rate']) * 100
        print(f"• Accepted papers have {diff:.1f}% higher false claim rate")
    else:
        diff = (rej['false_rate'] - acc['false_rate']) * 100
        print(f"• Rejected papers have {diff:.1f}% higher false claim rate")
    
    # Compare reviewer weights
    if acc['avg_weight'] > rej['avg_weight']:
        diff = acc['avg_weight'] - rej['avg_weight']
        print(f"• Accepted papers have {diff:.3f} higher average reviewer weight")
    else:
        diff = rej['avg_weight'] - acc['avg_weight']
        print(f"• Rejected papers have {diff:.3f} higher average reviewer weight")
    
    print()
    
    # Per-paper details
    print("6. PER-PAPER DETAILS")
    print("-"*70)
    for paper_id, result in sorted(results.items()):
        ground_truth = result.get('ground_truth')
        print(f"\n{paper_id} ({ground_truth}):")
        
        step1 = result.get('step1', {})
        if step1:
            print(f"  Step 1: {step1.get('num_claims', 0)} claims")
        
        step2 = result.get('step2', {})
        if step2:
            print(f"  Step 2: {step2.get('num_verified', 0)} verified | "
                  f"True: {step2.get('true_count', 0)} | "
                  f"False: {step2.get('false_count', 0)} | "
                  f"Partial: {step2.get('partial_count', 0)}")
        
        step3 = result.get('step3', {})
        if step3:
            print(f"  Step 3: {step3.get('num_reviewers', 0)} reviewers | "
                  f"Avg Weight: {step3.get('avg_weight', 0):.3f}")
    
    print()
    print("="*70)


def main():
    """Main function"""
    print("Loading results...")
    results = load_all_results()
    
    if not results:
        print("No ICLR 2024 results found.")
        return
    
    print(f"Found results for {len(results)} ICLR 2024 papers\n")
    
    comparison_stats = calculate_comparison_statistics(results)
    print_comparison_report(results, comparison_stats)
    
    # Save comparison report
    output_path = Path("data/results/iclr2024_comparison_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output = {
        'comparison_statistics': comparison_stats,
        'detailed_results': results
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\nComparison report saved to: {output_path}")


if __name__ == "__main__":
    main()


