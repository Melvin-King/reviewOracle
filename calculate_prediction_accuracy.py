"""
Calculate prediction accuracy based on pipeline results
Predicts paper acceptance/rejection and compares with ground truth
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
            verifications = json.load(f)
            if isinstance(verifications, list):
                verifications = {v['id']: v for v in verifications}
            data['verifications'] = verifications
    
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


def calculate_verification_score(verifications: Dict) -> float:
    """Calculate a score based on verification results"""
    if not verifications:
        return 0.5  # Neutral if no verifications
    
    true_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'True')
    false_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'False')
    partial_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'Partially_True')
    total = len(verifications)
    
    if total == 0:
        return 0.5
    
    # Score: True = 1.0, Partial = 0.5, False = 0.0
    score = (true_count * 1.0 + partial_count * 0.5 + false_count * 0.0) / total
    return score


def calculate_weighted_verification_score(verifications: Dict, weights: Dict) -> float:
    """Calculate weighted score considering reviewer weights"""
    if not verifications or not weights:
        return calculate_verification_score(verifications)
    
    # Group verifications by reviewer
    reviewer_scores = {}
    reviewer_weights = {}
    
    for claim_id, verification in verifications.items():
        # Extract reviewer ID from claim_id (e.g., "R1-C1" -> "R1")
        reviewer_id = claim_id.split('-')[0] if '-' in claim_id else None
        
        if reviewer_id and reviewer_id in weights:
            if reviewer_id not in reviewer_scores:
                reviewer_scores[reviewer_id] = []
                reviewer_weights[reviewer_id] = weights[reviewer_id].get('weight', 0.5)
            
            # Score: True = 1.0, Partial = 0.5, False = 0.0
            result = verification.get('verification_result', '')
            if result == 'True':
                reviewer_scores[reviewer_id].append(1.0)
            elif result == 'Partially_True':
                reviewer_scores[reviewer_id].append(0.5)
            else:
                reviewer_scores[reviewer_id].append(0.0)
    
    # Calculate weighted average
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
        return calculate_verification_score(verifications)


def predict_acceptance_method1(verifications: Dict) -> str:
    """Method 1: Predict based on true claim rate"""
    if not verifications:
        return "Unknown"
    
    true_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'True')
    false_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'False')
    total = len(verifications)
    
    if total == 0:
        return "Unknown"
    
    true_rate = true_count / total
    false_rate = false_count / total
    
    # If true rate > false rate, predict Accepted
    if true_rate > false_rate:
        return "Accepted"
    else:
        return "Rejected"


def predict_acceptance_method2(verifications: Dict, weights: Dict) -> str:
    """Method 2: Predict based on weighted verification score"""
    score = calculate_weighted_verification_score(verifications, weights)
    
    # Threshold: if score >= 0.5, predict Accepted
    if score >= 0.5:
        return "Accepted"
    else:
        return "Rejected"


def predict_acceptance_method3(verifications: Dict, weights: Dict) -> str:
    """Method 3: Predict based on weighted true claim rate"""
    if not verifications or not weights:
        return predict_acceptance_method1(verifications)
    
    # Group by reviewer and calculate weighted average
    reviewer_true_rates = {}
    reviewer_weights_dict = {}
    
    for claim_id, verification in verifications.items():
        reviewer_id = claim_id.split('-')[0] if '-' in claim_id else None
        
        if reviewer_id and reviewer_id in weights:
            if reviewer_id not in reviewer_true_rates:
                reviewer_true_rates[reviewer_id] = {'true': 0, 'total': 0}
                reviewer_weights_dict[reviewer_id] = weights[reviewer_id].get('weight', 0.5)
            
            reviewer_true_rates[reviewer_id]['total'] += 1
            if verification.get('verification_result') == 'True':
                reviewer_true_rates[reviewer_id]['true'] += 1
    
    # Calculate weighted average true rate
    total_weighted_true_rate = 0.0
    total_weight = 0.0
    
    for reviewer_id, rates in reviewer_true_rates.items():
        if rates['total'] > 0:
            true_rate = rates['true'] / rates['total']
            weight = reviewer_weights_dict[reviewer_id]
            total_weighted_true_rate += true_rate * weight
            total_weight += weight
    
    if total_weight > 0:
        avg_true_rate = total_weighted_true_rate / total_weight
        # Threshold: if avg_true_rate >= 0.25, predict Accepted
        if avg_true_rate >= 0.25:
            return "Accepted"
        else:
            return "Rejected"
    else:
        return predict_acceptance_method1(verifications)


def calculate_metrics(predictions: List[Tuple[str, str]]) -> Dict:
    """Calculate accuracy, precision, recall, F1"""
    # predictions: list of (ground_truth, prediction) tuples
    
    tp = 0  # True Positive: Predicted Accepted, Actually Accepted
    tn = 0  # True Negative: Predicted Rejected, Actually Rejected
    fp = 0  # False Positive: Predicted Accepted, Actually Rejected
    fn = 0  # False Negative: Predicted Rejected, Actually Accepted
    
    for ground_truth, prediction in predictions:
        if ground_truth == "Unknown":
            continue
        
        if prediction == "Accepted" and ground_truth == "Accepted":
            tp += 1
        elif prediction == "Rejected" and ground_truth == "Rejected":
            tn += 1
        elif prediction == "Accepted" and ground_truth == "Rejected":
            fp += 1
        elif prediction == "Rejected" and ground_truth == "Accepted":
            fn += 1
    
    total = tp + tn + fp + fn
    
    metrics = {
        'total': total,
        'tp': tp,
        'tn': tn,
        'fp': fp,
        'fn': fn,
        'accuracy': 0.0,
        'precision': 0.0,
        'recall': 0.0,
        'f1': 0.0
    }
    
    if total > 0:
        metrics['accuracy'] = (tp + tn) / total
    
    if (tp + fp) > 0:
        metrics['precision'] = tp / (tp + fp)
    
    if (tp + fn) > 0:
        metrics['recall'] = tp / (tp + fn)
    
    if metrics['precision'] + metrics['recall'] > 0:
        metrics['f1'] = 2 * (metrics['precision'] * metrics['recall']) / (metrics['precision'] + metrics['recall'])
    
    return metrics


def main():
    """Main function"""
    print("="*70)
    print("PREDICTION ACCURACY ANALYSIS")
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
    
    print(f"Found {len(paper_ids)} ICLR 2024 papers\n")
    
    # Load data for each paper
    papers_data = []
    for paper_id in paper_ids:
        data = load_paper_data(paper_id)
        if data['ground_truth'] != "Unknown":
            papers_data.append(data)
    
    print(f"Processing {len(papers_data)} papers with ground truth labels\n")
    
    # Make predictions using different methods
    methods = {
        'Method 1: True Claim Rate': predict_acceptance_method1,
        'Method 2: Weighted Verification Score': predict_acceptance_method2,
        'Method 3: Weighted True Rate': predict_acceptance_method3
    }
    
    all_results = {}
    
    for method_name, method_func in methods.items():
        print(f"{method_name}")
        print("-"*70)
        
        predictions = []
        paper_results = []
        
        for paper_data in papers_data:
            ground_truth = paper_data['ground_truth']
            verifications = paper_data['verifications']
            weights = paper_data['weights']
            
            if method_name == 'Method 1: True Claim Rate':
                prediction = method_func(verifications)
            else:
                prediction = method_func(verifications, weights)
            
            predictions.append((ground_truth, prediction))
            
            paper_results.append({
                'paper_id': paper_data['paper_id'],
                'ground_truth': ground_truth,
                'prediction': prediction,
                'correct': ground_truth == prediction
            })
            
            status = "✓" if ground_truth == prediction else "✗"
            print(f"  {status} {paper_data['paper_id']}: {ground_truth} -> {prediction}")
        
        # Calculate metrics
        metrics = calculate_metrics(predictions)
        
        print()
        print(f"  Accuracy: {metrics['accuracy']*100:.2f}%")
        print(f"  Precision: {metrics['precision']*100:.2f}%")
        print(f"  Recall: {metrics['recall']*100:.2f}%")
        print(f"  F1 Score: {metrics['f1']*100:.2f}%")
        print(f"  Confusion Matrix:")
        print(f"    TP: {metrics['tp']}, TN: {metrics['tn']}, FP: {metrics['fp']}, FN: {metrics['fn']}")
        print()
        
        all_results[method_name] = {
            'metrics': metrics,
            'paper_results': paper_results
        }
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print("Method Comparison:")
    print("-"*70)
    for method_name, results in all_results.items():
        metrics = results['metrics']
        print(f"{method_name}:")
        print(f"  Accuracy: {metrics['accuracy']*100:.2f}%")
        print(f"  F1 Score: {metrics['f1']*100:.2f}%")
        print()
    
    # Find best method
    best_method = max(all_results.items(), key=lambda x: x[1]['metrics']['accuracy'])
    print(f"Best Method: {best_method[0]}")
    print(f"  Accuracy: {best_method[1]['metrics']['accuracy']*100:.2f}%")
    print(f"  F1 Score: {best_method[1]['metrics']['f1']*100:.2f}%")
    print()
    
    # Save results
    output_path = Path("data/results/iclr2024_prediction_accuracy.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to: {output_path}")
    print("="*70)


if __name__ == "__main__":
    main()


