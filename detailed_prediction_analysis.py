"""
Detailed prediction analysis with per-paper scores
All outputs in English
"""

import sys
import io
import json
from pathlib import Path
from typing import Dict

# Set UTF-8 encoding for Windows
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass


def get_ground_truth_status(paper_id: str) -> str:
    """Get ground truth acceptance status"""
    accepted_path = Path(f"data/raw/iclr2024/papers/accepted/{paper_id}.pdf")
    rejected_path = Path(f"data/raw/iclr2024/papers/rejected/{paper_id}.pdf")
    
    if accepted_path.exists():
        return "Accepted"
    elif rejected_path.exists():
        return "Rejected"
    return "Unknown"


def calculate_weighted_verification_score(verifications: Dict, weights: Dict) -> float:
    """Calculate weighted verification score"""
    if not verifications or not weights:
        return 0.5
    
    reviewer_scores = {}
    reviewer_weights = {}
    
    for claim_id, verification in verifications.items():
        reviewer_id = claim_id.split('-')[0] if '-' in claim_id else None
        
        if reviewer_id and reviewer_id in weights:
            if reviewer_id not in reviewer_scores:
                reviewer_scores[reviewer_id] = []
                reviewer_weights[reviewer_id] = weights[reviewer_id].get('weight', 0.5)
            
            result = verification.get('verification_result', '')
            if result == 'True':
                reviewer_scores[reviewer_id].append(1.0)
            elif result == 'Partially_True':
                reviewer_scores[reviewer_id].append(0.5)
            else:
                reviewer_scores[reviewer_id].append(0.0)
    
    total_weighted_score = 0.0
    total_weight = 0.0
    
    for reviewer_id, scores in reviewer_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            weight = reviewer_weights[reviewer_id]
            total_weighted_score += avg_score * weight
            total_weight += weight
    
    if total_weight > 0:
        return total_weighted_score / total_weight
    else:
        return 0.5


def main():
    """Main function"""
    print("="*70)
    print("DETAILED PREDICTION ANALYSIS")
    print("="*70)
    print()
    
    # Find all ICLR papers
    accepted_dir = Path("data/raw/iclr2024/papers/accepted")
    rejected_dir = Path("data/raw/iclr2024/papers/rejected")
    
    paper_ids = []
    if accepted_dir.exists():
        paper_ids.extend([f.stem for f in accepted_dir.glob("*.pdf")])
    if rejected_dir.exists():
        paper_ids.extend([f.stem for f in rejected_dir.glob("*.pdf")])
    
    # Load data for each paper
    papers_data = []
    for paper_id in paper_ids:
        ground_truth = get_ground_truth_status(paper_id)
        if ground_truth == "Unknown":
            continue
        
        # Load verifications
        verifications_path = Path(f"data/results/verifications/{paper_id}_verified.json")
        verifications = {}
        if verifications_path.exists():
            with open(verifications_path, 'r', encoding='utf-8') as f:
                verifications_list = json.load(f)
                if isinstance(verifications_list, list):
                    verifications = {v['id']: v for v in verifications_list}
                else:
                    verifications = verifications_list
        
        # Load weights
        weights_path = Path(f"data/results/weights/{paper_id}_weights.json")
        weights = {}
        if weights_path.exists():
            with open(weights_path, 'r', encoding='utf-8') as f:
                weights = json.load(f)
        
        # Calculate scores
        weighted_score = calculate_weighted_verification_score(verifications, weights)
        
        # Count verification results
        true_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'True')
        false_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'False')
        partial_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'Partially_True')
        total_verified = len(verifications)
        
        # Calculate true rate
        true_rate = true_count / total_verified if total_verified > 0 else 0
        false_rate = false_count / total_verified if total_verified > 0 else 0
        
        # Prediction
        prediction = "Accepted" if weighted_score >= 0.5 else "Rejected"
        correct = prediction == ground_truth
        
        papers_data.append({
            'paper_id': paper_id,
            'ground_truth': ground_truth,
            'prediction': prediction,
            'correct': correct,
            'weighted_score': weighted_score,
            'true_rate': true_rate,
            'false_rate': false_rate,
            'true_count': true_count,
            'false_count': false_count,
            'partial_count': partial_count,
            'total_verified': total_verified,
            'avg_reviewer_weight': sum(w.get('weight', 0) for w in weights.values()) / len(weights) if weights else 0
        })
    
    # Sort by ground truth, then by score
    papers_data.sort(key=lambda x: (x['ground_truth'], -x['weighted_score']))
    
    # Print detailed results
    print("PER-PAPER DETAILED ANALYSIS")
    print("-"*70)
    print()
    
    print("ACCEPTED PAPERS:")
    print("-"*70)
    accepted_papers = [p for p in papers_data if p['ground_truth'] == 'Accepted']
    for paper in accepted_papers:
        status = "✓" if paper['correct'] else "✗"
        print(f"{status} {paper['paper_id']}")
        print(f"  Ground Truth: {paper['ground_truth']}")
        print(f"  Prediction: {paper['prediction']}")
        print(f"  Weighted Score: {paper['weighted_score']:.3f} (threshold: 0.5)")
        print(f"  Verification: {paper['total_verified']} total | "
              f"True: {paper['true_count']} ({paper['true_rate']*100:.1f}%) | "
              f"False: {paper['false_count']} ({paper['false_rate']*100:.1f}%) | "
              f"Partial: {paper['partial_count']}")
        print(f"  Avg Reviewer Weight: {paper['avg_reviewer_weight']:.3f}")
        print()
    
    print("REJECTED PAPERS:")
    print("-"*70)
    rejected_papers = [p for p in papers_data if p['ground_truth'] == 'Rejected']
    for paper in rejected_papers:
        status = "✓" if paper['correct'] else "✗"
        print(f"{status} {paper['paper_id']}")
        print(f"  Ground Truth: {paper['ground_truth']}")
        print(f"  Prediction: {paper['prediction']}")
        print(f"  Weighted Score: {paper['weighted_score']:.3f} (threshold: 0.5)")
        print(f"  Verification: {paper['total_verified']} total | "
              f"True: {paper['true_count']} ({paper['true_rate']*100:.1f}%) | "
              f"False: {paper['false_count']} ({paper['false_rate']*100:.1f}%) | "
              f"Partial: {paper['partial_count']}")
        print(f"  Avg Reviewer Weight: {paper['avg_reviewer_weight']:.3f}")
        print()
    
    # Summary statistics
    print("="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    print()
    
    correct = sum(1 for p in papers_data if p['correct'])
    total = len(papers_data)
    accuracy = correct / total if total > 0 else 0
    
    accepted_correct = sum(1 for p in accepted_papers if p['correct'])
    rejected_correct = sum(1 for p in rejected_papers if p['correct'])
    
    print(f"Overall Accuracy: {accuracy*100:.1f}% ({correct}/{total})")
    print(f"  Accepted Papers: {accepted_correct}/{len(accepted_papers)} correct ({accepted_correct/len(accepted_papers)*100:.1f}%)")
    print(f"  Rejected Papers: {rejected_correct}/{len(rejected_papers)} correct ({rejected_correct/len(rejected_papers)*100:.1f}%)")
    print()
    
    # Score distribution
    print("Score Distribution:")
    print("-"*70)
    accepted_scores = [p['weighted_score'] for p in accepted_papers]
    rejected_scores = [p['weighted_score'] for p in rejected_papers]
    
    if accepted_scores:
        print(f"Accepted Papers:")
        print(f"  Average Score: {sum(accepted_scores)/len(accepted_scores):.3f}")
        print(f"  Min Score: {min(accepted_scores):.3f}")
        print(f"  Max Score: {max(accepted_scores):.3f}")
        print(f"  Scores: {[f'{s:.3f}' for s in sorted(accepted_scores, reverse=True)]}")
    
    if rejected_scores:
        print(f"Rejected Papers:")
        print(f"  Average Score: {sum(rejected_scores)/len(rejected_scores):.3f}")
        print(f"  Min Score: {min(rejected_scores):.3f}")
        print(f"  Max Score: {max(rejected_scores):.3f}")
        print(f"  Scores: {[f'{s:.3f}' for s in sorted(rejected_scores, reverse=True)]}")
    
    print()
    print("="*70)


if __name__ == "__main__":
    main()

