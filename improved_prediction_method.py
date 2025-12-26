"""
Improved prediction method with multiple strategies
All outputs in English
"""

import sys
import io
import json
from pathlib import Path
from typing import Dict, List, Tuple

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


def load_paper_data(paper_id: str) -> Dict:
    """Load all data for a paper"""
    data = {
        'paper_id': paper_id,
        'ground_truth': get_ground_truth_status(paper_id),
        'verifications': {},
        'weights': {},
        'claims': []
    }
    
    # Load verifications
    verifications_path = Path(f"data/results/verifications/{paper_id}_verified.json")
    if verifications_path.exists():
        with open(verifications_path, 'r', encoding='utf-8') as f:
            verifications_list = json.load(f)
            if isinstance(verifications_list, list):
                data['verifications'] = {v['id']: v for v in verifications_list}
            else:
                data['verifications'] = verifications_list
    
    # Load weights
    weights_path = Path(f"data/results/weights/{paper_id}_weights.json")
    if weights_path.exists():
        with open(weights_path, 'r', encoding='utf-8') as f:
            data['weights'] = json.load(f)
    
    # Load claims
    claims_path = Path(f"data/processed/extracted/{paper_id}_claims.json")
    if claims_path.exists():
        with open(claims_path, 'r', encoding='utf-8') as f:
            data['claims'] = json.load(f)
    
    return data


def method_original(verifications: Dict, weights: Dict) -> Tuple[float, str]:
    """Original method: weighted verification score with 0.5 threshold"""
    if not verifications or not weights:
        return 0.5, "Unknown"
    
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
        score = total_weighted_score / total_weight
    else:
        score = 0.5
    
    prediction = "Accepted" if score >= 0.5 else "Rejected"
    return score, prediction


def method_adaptive_threshold(verifications: Dict, weights: Dict) -> Tuple[float, str]:
    """Method with adaptive threshold: lower for accepted papers"""
    score, _ = method_original(verifications, weights)
    
    # Use lower threshold (0.45) to reduce false negatives
    prediction = "Accepted" if score >= 0.45 else "Rejected"
    return score, prediction


def method_enhanced_partial(verifications: Dict, weights: Dict) -> Tuple[float, str]:
    """Enhanced method: give more weight to partial claims (0.7 instead of 0.5)"""
    if not verifications or not weights:
        return 0.5, "Unknown"
    
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
                reviewer_scores[reviewer_id].append(0.7)  # Increased from 0.5
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
        score = total_weighted_score / total_weight
    else:
        score = 0.5
    
    prediction = "Accepted" if score >= 0.5 else "Rejected"
    return score, prediction


def method_combined(claims: List[Dict], verifications: Dict, weights: Dict) -> Tuple[float, str]:
    """Combined method: verification score + sentiment balance"""
    if not claims or not verifications or not weights:
        return 0.5, "Unknown"
    
    # Calculate verification score (original method)
    verif_score, _ = method_original(verifications, weights)
    
    # Calculate sentiment balance (positive - negative, weighted)
    sentiment_map = {'Positive': 1.0, 'Neutral': 0.0, 'Negative': -1.0}
    sentiment_sum = 0.0
    sentiment_weight = 0.0
    
    for claim in claims:
        claim_id = claim.get('id', '')
        if claim_id not in verifications:
            continue
        
        reviewer_id = claim_id.split('-')[0] if '-' in claim_id else None
        if reviewer_id not in weights:
            continue
        
        # Only consider verified claims (True or Partially_True)
        verification_result = verifications[claim_id].get('verification_result', '')
        if verification_result == 'False':
            continue
        
        sentiment = claim.get('sentiment', 'Neutral')
        sentiment_value = sentiment_map.get(sentiment, 0.0)
        reviewer_weight = weights[reviewer_id].get('weight', 0.5)
        
        sentiment_sum += sentiment_value * reviewer_weight
        sentiment_weight += reviewer_weight
    
    if sentiment_weight > 0:
        sentiment_balance = sentiment_sum / sentiment_weight
        # Normalize to [0, 1]: (balance + 1) / 2
        sentiment_score = (sentiment_balance + 1) / 2
    else:
        sentiment_score = 0.5
    
    # Combine: 70% verification, 30% sentiment
    combined_score = 0.7 * verif_score + 0.3 * sentiment_score
    
    prediction = "Accepted" if combined_score >= 0.5 else "Rejected"
    return combined_score, prediction


def main():
    """Test improved prediction methods"""
    print("="*70)
    print("IMPROVED PREDICTION METHODS TEST")
    print("="*70)
    print()
    
    # Find all papers
    accepted_dir = Path("data/raw/iclr2024/papers/accepted")
    rejected_dir = Path("data/raw/iclr2024/papers/rejected")
    
    paper_ids = []
    if accepted_dir.exists():
        paper_ids.extend([f.stem for f in accepted_dir.glob("*.pdf")])
    if rejected_dir.exists():
        paper_ids.extend([f.stem for f in rejected_dir.glob("*.pdf")])
    
    # Load all paper data
    papers_data = []
    for paper_id in paper_ids:
        data = load_paper_data(paper_id)
        if data['ground_truth'] != "Unknown":
            papers_data.append(data)
    
    methods = {
        'Original (0.5 threshold)': method_original,
        'Adaptive Threshold (0.45)': method_adaptive_threshold,
        'Enhanced Partial (0.7 weight)': method_enhanced_partial,
        'Combined (70% verif + 30% sentiment)': method_combined
    }
    
    results = {}
    
    for method_name, method_func in methods.items():
        print(f"{method_name}")
        print("-"*70)
        
        correct = 0
        total = len(papers_data)
        predictions = []
        
        for paper_data in papers_data:
            if method_name == 'Combined (70% verif + 30% sentiment)':
                score, prediction = method_func(
                    paper_data['claims'],
                    paper_data['verifications'],
                    paper_data['weights']
                )
            else:
                score, prediction = method_func(
                    paper_data['verifications'],
                    paper_data['weights']
                )
            
            ground_truth = paper_data['ground_truth']
            is_correct = prediction == ground_truth
            
            if is_correct:
                correct += 1
            
            predictions.append({
                'paper_id': paper_data['paper_id'],
                'ground_truth': ground_truth,
                'prediction': prediction,
                'score': score,
                'correct': is_correct
            })
            
            status = "✓" if is_correct else "✗"
            print(f"  {status} {paper_data['paper_id']}: {ground_truth} -> {prediction} (score: {score:.3f})")
        
        accuracy = correct / total if total > 0 else 0
        print(f"\n  Accuracy: {accuracy*100:.1f}% ({correct}/{total})")
        print()
        
        results[method_name] = {
            'accuracy': accuracy,
            'correct': correct,
            'total': total,
            'predictions': predictions
        }
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print("Method Comparison:")
    print("-"*70)
    for method_name, result in results.items():
        print(f"{method_name}: {result['accuracy']*100:.1f}%")
    
    best_method = max(results.items(), key=lambda x: x[1]['accuracy'])
    print(f"\nBest Method: {best_method[0]}")
    print(f"  Accuracy: {best_method[1]['accuracy']*100:.1f}%")
    
    # Show errors for best method
    print(f"\nErrors in Best Method:")
    for pred in best_method[1]['predictions']:
        if not pred['correct']:
            print(f"  {pred['paper_id']}: {pred['ground_truth']} -> {pred['prediction']} (score: {pred['score']:.3f})")
    
    print("\n" + "="*70)
    
    # Save results
    output_path = Path("data/results/iclr2024_improved_prediction.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()

