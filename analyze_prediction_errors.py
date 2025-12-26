"""
Analyze prediction errors and explore correction methods
All outputs in English
"""

import sys
import io
import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

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


def analyze_paper_details(paper_id: str) -> Dict:
    """Analyze detailed metrics for a paper"""
    ground_truth = get_ground_truth_status(paper_id)
    
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
    
    # Load claims
    claims_path = Path(f"data/processed/extracted/{paper_id}_claims.json")
    claims = []
    if claims_path.exists():
        with open(claims_path, 'r', encoding='utf-8') as f:
            claims = json.load(f)
    
    # Calculate metrics
    weighted_score = calculate_weighted_verification_score(verifications, weights)
    
    # Count verification results
    true_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'True')
    false_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'False')
    partial_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'Partially_True')
    total_verified = len(verifications)
    
    # Calculate rates
    true_rate = true_count / total_verified if total_verified > 0 else 0
    false_rate = false_count / total_verified if total_verified > 0 else 0
    partial_rate = partial_count / total_verified if total_verified > 0 else 0
    
    # Analyze sentiment distribution
    positive_claims = sum(1 for c in claims if c.get('sentiment') == 'Positive')
    negative_claims = sum(1 for c in claims if c.get('sentiment') == 'Negative')
    neutral_claims = sum(1 for c in claims if c.get('sentiment') == 'Neutral')
    total_claims = len(claims)
    
    # Calculate reviewer statistics
    reviewer_stats = {}
    for reviewer_id, weight_data in weights.items():
        reviewer_claims = [c for c in claims if c.get('id', '').startswith(reviewer_id)]
        reviewer_verifications = {k: v for k, v in verifications.items() if k.startswith(reviewer_id)}
        
        reviewer_true = sum(1 for v in reviewer_verifications.values() if v.get('verification_result') == 'True')
        reviewer_false = sum(1 for v in reviewer_verifications.values() if v.get('verification_result') == 'False')
        reviewer_partial = sum(1 for v in reviewer_verifications.values() if v.get('verification_result') == 'Partially_True')
        reviewer_total = len(reviewer_verifications)
        
        reviewer_stats[reviewer_id] = {
            'weight': weight_data.get('weight', 0),
            'num_claims': len(reviewer_claims),
            'num_verified': reviewer_total,
            'true_count': reviewer_true,
            'false_count': reviewer_false,
            'partial_count': reviewer_partial,
            'true_rate': reviewer_true / reviewer_total if reviewer_total > 0 else 0,
            'positive_claims': sum(1 for c in reviewer_claims if c.get('sentiment') == 'Positive'),
            'negative_claims': sum(1 for c in reviewer_claims if c.get('sentiment') == 'Negative')
        }
    
    return {
        'paper_id': paper_id,
        'ground_truth': ground_truth,
        'weighted_score': weighted_score,
        'total_claims': total_claims,
        'total_verified': total_verified,
        'true_count': true_count,
        'false_count': false_count,
        'partial_count': partial_count,
        'true_rate': true_rate,
        'false_rate': false_rate,
        'partial_rate': partial_rate,
        'positive_claims': positive_claims,
        'negative_claims': negative_claims,
        'neutral_claims': neutral_claims,
        'reviewer_stats': reviewer_stats,
        'avg_reviewer_weight': sum(w.get('weight', 0) for w in weights.values()) / len(weights) if weights else 0
    }


def main():
    """Main function"""
    print("="*70)
    print("PREDICTION ERROR ANALYSIS")
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
    
    # Analyze all papers
    all_papers_data = []
    for paper_id in paper_ids:
        data = analyze_paper_details(paper_id)
        if data['ground_truth'] != "Unknown":
            all_papers_data.append(data)
    
    # Identify errors (Method 2: Weighted Verification Score)
    threshold = 0.5
    errors = []
    correct = []
    
    for paper_data in all_papers_data:
        prediction = "Accepted" if paper_data['weighted_score'] >= threshold else "Rejected"
        is_correct = prediction == paper_data['ground_truth']
        
        if is_correct:
            correct.append(paper_data)
        else:
            errors.append(paper_data)
    
    print(f"Total Papers: {len(all_papers_data)}")
    print(f"Correct Predictions: {len(correct)}")
    print(f"Error Predictions: {len(errors)}")
    print()
    
    # Analyze errors
    print("="*70)
    print("ERROR ANALYSIS")
    print("="*70)
    print()
    
    for error in errors:
        prediction = "Accepted" if error['weighted_score'] >= threshold else "Rejected"
        print(f"Paper: {error['paper_id']}")
        print(f"  Ground Truth: {error['ground_truth']}")
        print(f"  Prediction: {prediction} (Score: {error['weighted_score']:.3f}, Threshold: {threshold})")
        print(f"  Score Difference: {error['weighted_score'] - threshold:.3f}")
        print()
        print(f"  Verification Stats:")
        print(f"    Total Verified: {error['total_verified']}")
        print(f"    True: {error['true_count']} ({error['true_rate']*100:.1f}%)")
        print(f"    False: {error['false_count']} ({error['false_rate']*100:.1f}%)")
        print(f"    Partial: {error['partial_count']} ({error['partial_rate']*100:.1f}%)")
        print()
        print(f"  Claim Sentiment:")
        print(f"    Positive: {error['positive_claims']} ({error['positive_claims']/error['total_claims']*100:.1f}%)")
        print(f"    Negative: {error['negative_claims']} ({error['negative_claims']/error['total_claims']*100:.1f}%)")
        print(f"    Neutral: {error['neutral_claims']} ({error['neutral_claims']/error['total_claims']*100:.1f}%)")
        print()
        print(f"  Reviewer Stats:")
        for reviewer_id, stats in error['reviewer_stats'].items():
            print(f"    {reviewer_id}: Weight={stats['weight']:.3f}, "
                  f"Claims={stats['num_claims']}, "
                  f"True Rate={stats['true_rate']*100:.1f}%, "
                  f"Pos={stats['positive_claims']}, Neg={stats['negative_claims']}")
        print()
        print("-"*70)
        print()
    
    # Compare with correct predictions
    print("="*70)
    print("COMPARISON: ERRORS vs CORRECT")
    print("="*70)
    print()
    
    if errors:
        error_avg_score = sum(e['weighted_score'] for e in errors) / len(errors)
        error_avg_true_rate = sum(e['true_rate'] for e in errors) / len(errors)
        error_avg_partial_rate = sum(e['partial_rate'] for e in errors) / len(errors)
        error_avg_positive = sum(e['positive_claims']/e['total_claims'] for e in errors) / len(errors)
        
        print("Error Papers (Average):")
        print(f"  Weighted Score: {error_avg_score:.3f}")
        print(f"  True Rate: {error_avg_true_rate*100:.1f}%")
        print(f"  Partial Rate: {error_avg_partial_rate*100:.1f}%")
        print(f"  Positive Claim Rate: {error_avg_positive*100:.1f}%")
        print()
    
    if correct:
        correct_avg_score = sum(c['weighted_score'] for c in correct) / len(correct)
        correct_avg_true_rate = sum(c['true_rate'] for c in correct) / len(correct)
        correct_avg_partial_rate = sum(c['partial_rate'] for c in correct) / len(correct)
        correct_avg_positive = sum(c['positive_claims']/c['total_claims'] for c in correct) / len(correct)
        
        print("Correct Papers (Average):")
        print(f"  Weighted Score: {correct_avg_score:.3f}")
        print(f"  True Rate: {correct_avg_true_rate*100:.1f}%")
        print(f"  Partial Rate: {correct_avg_partial_rate*100:.1f}%")
        print(f"  Positive Claim Rate: {correct_avg_positive*100:.1f}%")
        print()
    
    # Test different thresholds
    print("="*70)
    print("THRESHOLD OPTIMIZATION")
    print("="*70)
    print()
    
    best_threshold = threshold
    best_accuracy = len(correct) / len(all_papers_data)
    
    for test_threshold in [0.40, 0.42, 0.44, 0.46, 0.48, 0.50, 0.52, 0.54, 0.56]:
        tp = sum(1 for p in all_papers_data 
                 if p['ground_truth'] == "Accepted" and p['weighted_score'] >= test_threshold)
        tn = sum(1 for p in all_papers_data 
                 if p['ground_truth'] == "Rejected" and p['weighted_score'] < test_threshold)
        accuracy = (tp + tn) / len(all_papers_data)
        
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_threshold = test_threshold
        
        print(f"Threshold {test_threshold:.2f}: Accuracy = {accuracy*100:.1f}% "
              f"(TP={tp}, TN={tn})")
    
    print()
    print(f"Best Threshold: {best_threshold:.2f} (Accuracy: {best_accuracy*100:.1f}%)")
    print()
    
    # Test alternative scoring methods
    print("="*70)
    print("ALTERNATIVE SCORING METHODS")
    print("="*70)
    print()
    
    # Method A: Adjust for partial claims (treat partial as 0.6 instead of 0.5)
    print("Method A: Treat Partial as 0.6 (instead of 0.5)")
    def calculate_adjusted_score(verifications, weights, partial_weight=0.6):
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
                    reviewer_scores[reviewer_id].append(partial_weight)
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
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.5
    
    for partial_weight in [0.55, 0.60, 0.65]:
        adjusted_scores = []
        for paper_data in all_papers_data:
            verifications_path = Path(f"data/results/verifications/{paper_data['paper_id']}_verified.json")
            weights_path = Path(f"data/results/weights/{paper_data['paper_id']}_weights.json")
            
            verifications = {}
            if verifications_path.exists():
                with open(verifications_path, 'r', encoding='utf-8') as f:
                    verifications_list = json.load(f)
                    if isinstance(verifications_list, list):
                        verifications = {v['id']: v for v in verifications_list}
                    else:
                        verifications = verifications_list
            
            weights = {}
            if weights_path.exists():
                with open(weights_path, 'r', encoding='utf-8') as f:
                    weights = json.load(f)
            
            adjusted_score = calculate_adjusted_score(verifications, weights, partial_weight)
            adjusted_scores.append((paper_data['paper_id'], paper_data['ground_truth'], adjusted_score))
        
        # Calculate accuracy with threshold 0.5
        tp = sum(1 for pid, gt, score in adjusted_scores if gt == "Accepted" and score >= 0.5)
        tn = sum(1 for pid, gt, score in adjusted_scores if gt == "Rejected" and score < 0.5)
        accuracy = (tp + tn) / len(adjusted_scores)
        
        print(f"  Partial Weight {partial_weight:.2f}: Accuracy = {accuracy*100:.1f}%")
    
    print()
    
    # Method B: Include sentiment in score calculation
    print("Method B: Include Sentiment Weight")
    def calculate_sentiment_weighted_score(claims, verifications, weights):
        if not claims or not verifications or not weights:
            return 0.5
        
        reviewer_contributions = defaultdict(lambda: {'weighted_sum': 0.0, 'total_weight': 0.0})
        
        for claim in claims:
            claim_id = claim.get('id', '')
            reviewer_id = claim_id.split('-')[0] if '-' in claim_id else None
            
            if reviewer_id and reviewer_id in weights and claim_id in verifications:
                verification = verifications[claim_id]
                result = verification.get('verification_result', '')
                
                # Base score from verification
                if result == 'True':
                    base_score = 1.0
                elif result == 'Partially_True':
                    base_score = 0.5
                else:
                    base_score = 0.0
                
                # Sentiment multiplier (positive claims get bonus)
                sentiment = claim.get('sentiment', 'Neutral')
                if sentiment == 'Positive':
                    sentiment_mult = 1.1
                elif sentiment == 'Negative':
                    sentiment_mult = 0.9
                else:
                    sentiment_mult = 1.0
                
                adjusted_score = base_score * sentiment_mult
                weight = weights[reviewer_id].get('weight', 0.5)
                
                reviewer_contributions[reviewer_id]['weighted_sum'] += adjusted_score * weight
                reviewer_contributions[reviewer_id]['total_weight'] += weight
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for reviewer_id, contrib in reviewer_contributions.items():
            if contrib['total_weight'] > 0:
                reviewer_avg = contrib['weighted_sum'] / contrib['total_weight']
                total_weighted_score += reviewer_avg * contrib['total_weight']
                total_weight += contrib['total_weight']
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.5
    
    sentiment_scores = []
    for paper_data in all_papers_data:
        claims_path = Path(f"data/processed/extracted/{paper_data['paper_id']}_claims.json")
        verifications_path = Path(f"data/results/verifications/{paper_data['paper_id']}_verified.json")
        weights_path = Path(f"data/results/weights/{paper_data['paper_id']}_weights.json")
        
        claims = []
        if claims_path.exists():
            with open(claims_path, 'r', encoding='utf-8') as f:
                claims = json.load(f)
        
        verifications = {}
        if verifications_path.exists():
            with open(verifications_path, 'r', encoding='utf-8') as f:
                verifications_list = json.load(f)
                if isinstance(verifications_list, list):
                    verifications = {v['id']: v for v in verifications_list}
                else:
                    verifications = verifications_list
        
        weights = {}
        if weights_path.exists():
            with open(weights_path, 'r', encoding='utf-8') as f:
                weights = json.load(f)
        
        sentiment_score = calculate_sentiment_weighted_score(claims, verifications, weights)
        sentiment_scores.append((paper_data['paper_id'], paper_data['ground_truth'], sentiment_score))
    
    tp = sum(1 for pid, gt, score in sentiment_scores if gt == "Accepted" and score >= 0.5)
    tn = sum(1 for pid, gt, score in sentiment_scores if gt == "Rejected" and score < 0.5)
    accuracy = (tp + tn) / len(sentiment_scores)
    
    print(f"  Sentiment Weighted: Accuracy = {accuracy*100:.1f}%")
    print()
    
    print("="*70)


if __name__ == "__main__":
    main()
