"""
Analyze ICLR 2024 pipeline results and compare with ground truth
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


def get_paper_status(paper_id):
    """Get ground truth status from file location"""
    accepted_path = Path(f"data/raw/iclr2024/papers/accepted/{paper_id}.pdf")
    rejected_path = Path(f"data/raw/iclr2024/papers/rejected/{paper_id}.pdf")
    
    if accepted_path.exists():
        return "Accepted"
    elif rejected_path.exists():
        return "Rejected"
    return "Unknown"


def load_results():
    """Load all pipeline results"""
    results = {}
    
    # Get all processed papers
    claims_dir = Path("data/processed/extracted")
    verifications_dir = Path("data/results/verifications")
    weights_dir = Path("data/results/weights")
    
    # Find all paper IDs
    paper_ids = set()
    for claims_file in claims_dir.glob("*_claims.json"):
        paper_id = claims_file.stem.replace("_claims", "")
        paper_ids.add(paper_id)
    
    for paper_id in paper_ids:
        result = {
            'paper_id': paper_id,
            'ground_truth': get_paper_status(paper_id),
            'step1': {},
            'step2': {},
            'step3': {}
        }
        
        # Load Step 1 results
        claims_file = claims_dir / f"{paper_id}_claims.json"
        if claims_file.exists():
            with open(claims_file, 'r', encoding='utf-8') as f:
                claims = json.load(f)
                result['step1'] = {
                    'success': True,
                    'num_claims': len(claims),
                    'claims_by_topic': defaultdict(int),
                    'claims_by_sentiment': defaultdict(int),
                    'claims_by_evidence': defaultdict(int)
                }
                for claim in claims:
                    result['step1']['claims_by_topic'][claim.get('topic', 'Unknown')] += 1
                    result['step1']['claims_by_sentiment'][claim.get('sentiment', 'Unknown')] += 1
                    result['step1']['claims_by_evidence'][claim.get('substantiation_type', 'None')] += 1
        
        # Load Step 2 results
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
                    'success': True,
                    'num_verified': len(verifications),
                    'true_count': true_count,
                    'false_count': false_count,
                    'partial_count': partial_count
                }
        
        # Load Step 3 results
        weights_file = weights_dir / f"{paper_id}_weights.json"
        if weights_file.exists():
            with open(weights_file, 'r', encoding='utf-8') as f:
                weights = json.load(f)
                result['step3'] = {
                    'success': True,
                    'num_reviewers': len(weights),
                    'weights': {k: v.get('weight', 0) for k, v in weights.items()},
                    'avg_weight': sum(v.get('weight', 0) for v in weights.values()) / len(weights) if weights else 0
                }
        
        results[paper_id] = result
    
    return results


def calculate_statistics(results):
    """Calculate overall statistics"""
    stats = {
        'total_papers': len(results),
        'accepted_papers': 0,
        'rejected_papers': 0,
        'step1_success': 0,
        'step2_success': 0,
        'step3_success': 0,
        'total_claims': 0,
        'total_verified': 0,
        'total_true': 0,
        'total_false': 0,
        'total_partial': 0,
        'total_reviewers': 0,
        'avg_weight_accepted': [],
        'avg_weight_rejected': [],
        'claims_by_topic': defaultdict(int),
        'claims_by_sentiment': defaultdict(int),
        'claims_by_evidence': defaultdict(int)
    }
    
    for paper_id, result in results.items():
        ground_truth = result.get('ground_truth', 'Unknown')
        if ground_truth == 'Accepted':
            stats['accepted_papers'] += 1
        elif ground_truth == 'Rejected':
            stats['rejected_papers'] += 1
        
        # Step 1
        if result.get('step1', {}).get('success'):
            stats['step1_success'] += 1
            stats['total_claims'] += result['step1'].get('num_claims', 0)
            for topic, count in result['step1'].get('claims_by_topic', {}).items():
                stats['claims_by_topic'][topic] += count
            for sentiment, count in result['step1'].get('claims_by_sentiment', {}).items():
                stats['claims_by_sentiment'][sentiment] += count
            for evidence, count in result['step1'].get('claims_by_evidence', {}).items():
                stats['claims_by_evidence'][evidence] += count
        
        # Step 2
        if result.get('step2', {}).get('success'):
            stats['step2_success'] += 1
            stats['total_verified'] += result['step2'].get('num_verified', 0)
            stats['total_true'] += result['step2'].get('true_count', 0)
            stats['total_false'] += result['step2'].get('false_count', 0)
            stats['total_partial'] += result['step2'].get('partial_count', 0)
        
        # Step 3
        if result.get('step3', {}).get('success'):
            stats['step3_success'] += 1
            stats['total_reviewers'] += result['step3'].get('num_reviewers', 0)
            avg_weight = result['step3'].get('avg_weight', 0)
            if ground_truth == 'Accepted':
                stats['avg_weight_accepted'].append(avg_weight)
            elif ground_truth == 'Rejected':
                stats['avg_weight_rejected'].append(avg_weight)
    
    return stats


def print_statistics(stats, results):
    """Print comprehensive statistics"""
    print("="*70)
    print("ICLR 2024 PIPELINE RESULTS STATISTICS")
    print("="*70)
    print()
    
    # Overall statistics
    print("1. OVERALL STATISTICS")
    print("-"*70)
    print(f"Total Papers Processed: {stats['total_papers']}")
    print(f"  - Accepted Papers: {stats['accepted_papers']}")
    print(f"  - Rejected Papers: {stats['rejected_papers']}")
    print()
    
    # Step 1 statistics
    print("2. STEP 1: CLAIM EXTRACTION")
    print("-"*70)
    print(f"Success Rate: {stats['step1_success']}/{stats['total_papers']} ({stats['step1_success']/stats['total_papers']*100:.1f}%)")
    print(f"Total Claims Extracted: {stats['total_claims']}")
    if stats['total_papers'] > 0:
        print(f"Average Claims per Paper: {stats['total_claims']/stats['step1_success']:.1f}" if stats['step1_success'] > 0 else "N/A")
    print()
    
    if stats['claims_by_topic']:
        print("Claims by Topic:")
        for topic, count in sorted(stats['claims_by_topic'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {topic}: {count} ({count/stats['total_claims']*100:.1f}%)")
        print()
    
    if stats['claims_by_sentiment']:
        print("Claims by Sentiment:")
        for sentiment, count in sorted(stats['claims_by_sentiment'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {sentiment}: {count} ({count/stats['total_claims']*100:.1f}%)")
        print()
    
    if stats['claims_by_evidence']:
        print("Claims by Evidence Type:")
        for evidence, count in sorted(stats['claims_by_evidence'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {evidence}: {count} ({count/stats['total_claims']*100:.1f}%)")
        print()
    
    # Step 2 statistics
    print("3. STEP 2: FACT VERIFICATION")
    print("-"*70)
    print(f"Success Rate: {stats['step2_success']}/{stats['total_papers']} ({stats['step2_success']/stats['total_papers']*100:.1f}%)")
    print(f"Total Claims Verified: {stats['total_verified']}")
    print(f"  - True: {stats['total_true']} ({stats['total_true']/stats['total_verified']*100:.1f}%)" if stats['total_verified'] > 0 else "  - True: 0")
    print(f"  - False: {stats['total_false']} ({stats['total_false']/stats['total_verified']*100:.1f}%)" if stats['total_verified'] > 0 else "  - False: 0")
    print(f"  - Partially True: {stats['total_partial']} ({stats['total_partial']/stats['total_verified']*100:.1f}%)" if stats['total_verified'] > 0 else "  - Partially True: 0")
    print()
    
    # Step 3 statistics
    print("4. STEP 3: REVIEWER WEIGHTING")
    print("-"*70)
    print(f"Success Rate: {stats['step3_success']}/{stats['total_papers']} ({stats['step3_success']/stats['total_papers']*100:.1f}%)")
    print(f"Total Reviewers: {stats['total_reviewers']}")
    if stats['total_papers'] > 0:
        print(f"Average Reviewers per Paper: {stats['total_reviewers']/stats['step3_success']:.1f}" if stats['step3_success'] > 0 else "N/A")
    print()
    
    if stats['avg_weight_accepted']:
        avg_accepted = sum(stats['avg_weight_accepted']) / len(stats['avg_weight_accepted'])
        print(f"Average Reviewer Weight (Accepted Papers): {avg_accepted:.3f}")
    
    if stats['avg_weight_rejected']:
        avg_rejected = sum(stats['avg_weight_rejected']) / len(stats['avg_weight_rejected'])
        print(f"Average Reviewer Weight (Rejected Papers): {avg_rejected:.3f}")
    print()
    
    # Per-paper breakdown
    print("5. PER-PAPER BREAKDOWN")
    print("-"*70)
    for paper_id, result in sorted(results.items()):
        ground_truth = result.get('ground_truth', 'Unknown')
        print(f"\nPaper: {paper_id} ({ground_truth})")
        
        step1 = result.get('step1', {})
        if step1.get('success'):
            print(f"  Step 1: {step1.get('num_claims', 0)} claims extracted")
        
        step2 = result.get('step2', {})
        if step2.get('success'):
            print(f"  Step 2: {step2.get('num_verified', 0)} verified (T:{step2.get('true_count', 0)}, F:{step2.get('false_count', 0)}, P:{step2.get('partial_count', 0)})")
        
        step3 = result.get('step3', {})
        if step3.get('success'):
            print(f"  Step 3: {step3.get('num_reviewers', 0)} reviewers, avg weight: {step3.get('avg_weight', 0):.3f}")
    
    print()
    print("="*70)


def main():
    """Main function"""
    print("Loading results...")
    results = load_results()
    
    if not results:
        print("No results found. Please run the pipeline first.")
        return
    
    print(f"Found results for {len(results)} papers\n")
    
    stats = calculate_statistics(results)
    print_statistics(stats, results)
    
    # Save statistics
    output_path = Path("data/results/iclr2024_statistics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output = {
        'statistics': stats,
        'detailed_results': results
    }
    
    # Convert defaultdict to dict for JSON serialization
    stats_serializable = dict(stats)
    stats_serializable['claims_by_topic'] = dict(stats['claims_by_topic'])
    stats_serializable['claims_by_sentiment'] = dict(stats['claims_by_sentiment'])
    stats_serializable['claims_by_evidence'] = dict(stats['claims_by_evidence'])
    output['statistics'] = stats_serializable
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\nStatistics saved to: {output_path}")


if __name__ == "__main__":
    main()


