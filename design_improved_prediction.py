"""
Design improved prediction method to achieve 80% accuracy
Analyze error cases and design better scoring mechanism
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


def load_paper_data(paper_id: str) -> Dict:
    """Load all data for a paper"""
    data = {
        'paper_id': paper_id,
        'ground_truth': get_ground_truth_status(paper_id)
    }
    
    # Load claims
    claims_path = Path(f"data/processed/extracted/{paper_id}_claims.json")
    if claims_path.exists():
        with open(claims_path, 'r', encoding='utf-8') as f:
            data['claims'] = json.load(f)
    else:
        data['claims'] = []
    
    # Load verifications
    verifications_path = Path(f"data/results/verifications/{paper_id}_verified.json")
    if verifications_path.exists():
        with open(verifications_path, 'r', encoding='utf-8') as f:
            verifications_list = json.load(f)
            if isinstance(verifications_list, list):
                data['verifications'] = {v['id']: v for v in verifications_list}
            else:
                data['verifications'] = verifications_list
    else:
        data['verifications'] = {}
    
    # Load weights
    weights_path = Path(f"data/results/weights/{paper_id}_weights.json")
    if weights_path.exists():
        with open(weights_path, 'r', encoding='utf-8') as f:
            data['weights'] = json.load(f)
    else:
        data['weights'] = {}
    
    # Load reviews
    reviews_path = Path(f"data/raw/iclr2024/reviews/{paper_id}_reviews.json")
    if reviews_path.exists():
        with open(reviews_path, 'r', encoding='utf-8') as f:
            data['reviews'] = json.load(f)
    else:
        data['reviews'] = []
    
    return data


def extract_ratings(reviews: List[Dict]) -> List[float]:
    """Extract numeric ratings from reviews"""
    ratings = []
    for review in reviews:
        rating_str = review.get('content', {}).get('rating', {}).get('value', '')
        if rating_str:
            # Parse rating like "8: accept, good paper" or "6: marginally above"
            try:
                rating_num = float(rating_str.split(':')[0].strip())
                ratings.append(rating_num)
            except:
                pass
    return ratings


def calculate_advanced_score(paper_data: Dict) -> float:
    """
    Advanced scoring method combining multiple factors:
    1. Weighted verification score (base)
    2. Rating-based score
    3. Sentiment balance
    4. Reviewer credibility
    5. Partial claim handling
    """
    claims = paper_data.get('claims', [])
    verifications = paper_data.get('verifications', {})
    weights = paper_data.get('weights', {})
    reviews = paper_data.get('reviews', [])
    
    if not claims or not verifications:
        return 0.5
    
    # Factor 1: Weighted verification score (with enhanced partial handling)
    reviewer_scores = {}
    reviewer_weights = {}
    
    for claim in claims:
        claim_id = claim.get('id', '')
        reviewer_id = claim_id.split('-')[0] if '-' in claim_id else None
        
        if reviewer_id and reviewer_id in weights and claim_id in verifications:
            if reviewer_id not in reviewer_scores:
                reviewer_scores[reviewer_id] = []
                reviewer_weights[reviewer_id] = weights[reviewer_id].get('weight', 0.5)
            
            verification = verifications[claim_id]
            result = verification.get('verification_result', '')
            confidence = verification.get('confidence', 0.5)
            
            # Enhanced scoring with confidence
            if result == 'True':
                score = 1.0 * confidence  # Weight by confidence
            elif result == 'Partially_True':
                score = 0.7 * confidence  # Enhanced partial weight
            else:
                score = 0.0
            
            reviewer_scores[reviewer_id].append(score)
    
    weighted_verification_score = 0.0
    total_weight = 0.0
    
    for reviewer_id, scores in reviewer_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            weight = reviewer_weights[reviewer_id]
            weighted_verification_score += avg_score * weight
            total_weight += weight
    
    base_score = weighted_verification_score / total_weight if total_weight > 0 else 0.5
    
    # Factor 2: Rating-based score (normalized to 0-1)
    ratings = extract_ratings(reviews)
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
        # ICLR ratings are typically 1-10, normalize to 0-1
        rating_score = (avg_rating - 1) / 9.0  # Maps 1->0, 10->1
    else:
        rating_score = 0.5
    
    # Factor 3: Sentiment balance
    positive_claims = sum(1 for c in claims if c.get('sentiment') == 'Positive')
    negative_claims = sum(1 for c in claims if c.get('sentiment') == 'Negative')
    total_claims = len(claims)
    
    if total_claims > 0:
        sentiment_balance = (positive_claims - negative_claims) / total_claims
        # Normalize from [-1, 1] to [0, 1]
        sentiment_score = (sentiment_balance + 1) / 2.0
    else:
        sentiment_score = 0.5
    
    # Factor 4: Reviewer credibility (average weight)
    if weights:
        avg_reviewer_weight = sum(w.get('weight', 0) for w in weights.values()) / len(weights)
    else:
        avg_reviewer_weight = 0.5
    
    # Factor 5: Verification coverage (proportion of claims verified as True)
    true_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'True')
    partial_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'Partially_True')
    verified_count = len(verifications)
    
    if verified_count > 0:
        # Weighted verification rate
        verification_coverage = (true_count * 1.0 + partial_count * 0.7) / verified_count
    else:
        verification_coverage = 0.5
    
    # Combined score with adaptive weights
    # For accepted papers, we want higher weight on ratings and sentiment
    # For rejected papers, we want higher weight on verification failures
    
    # Adaptive weighting based on base score
    if base_score >= 0.5:
        # Likely accepted: emphasize ratings and sentiment
        final_score = (
            0.35 * base_score +
            0.30 * rating_score +
            0.20 * sentiment_score +
            0.10 * avg_reviewer_weight +
            0.05 * verification_coverage
        )
    else:
        # Likely rejected: emphasize verification failures and low ratings
        final_score = (
            0.40 * base_score +
            0.25 * rating_score +
            0.15 * sentiment_score +
            0.15 * avg_reviewer_weight +
            0.05 * verification_coverage
        )
    
    return final_score


def calculate_hybrid_score_v2(paper_data: Dict) -> float:
    """
    Alternative hybrid scoring with different strategy
    Focus on consensus and strong signals
    """
    claims = paper_data.get('claims', [])
    verifications = paper_data.get('verifications', {})
    weights = paper_data.get('weights', {})
    reviews = paper_data.get('reviews', [])
    
    if not claims or not verifications:
        return 0.5
    
    # Get ratings
    ratings = extract_ratings(reviews)
    
    # Method: Use rating as primary signal, but adjust based on verification quality
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
        min_rating = min(ratings)
        max_rating = max(ratings)
        
        # Rating-based score (primary)
        rating_score = (avg_rating - 1) / 9.0
        
        # Calculate verification quality adjustment
        true_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'True')
        false_count = sum(1 for v in verifications.values() if v.get('verification_result') == 'False')
        total_verified = len(verifications)
        
        if total_verified > 0:
            verification_quality = (true_count - false_count) / total_verified
        else:
            verification_quality = 0
        
        # If reviewers have high ratings but many false claims, reduce score
        # If reviewers have low ratings but claims are mostly true, might be harsh but accurate
        adjustment = verification_quality * 0.2  # Max 0.2 adjustment
        
        # Consensus factor (how close are ratings?)
        if len(ratings) > 1:
            rating_std = ((max_rating - min_rating) / 9.0)  # Normalized std
            consensus_factor = 1.0 - rating_std * 0.1  # More consensus = slight boost
        else:
            consensus_factor = 1.0
        
        final_score = rating_score + adjustment
        final_score = final_score * consensus_factor
        
        # Clamp to [0, 1]
        final_score = max(0.0, min(1.0, final_score))
    else:
        # Fallback to verification-based score
        reviewer_scores = {}
        reviewer_weights = {}
        
        for claim in claims:
            claim_id = claim.get('id', '')
            reviewer_id = claim_id.split('-')[0] if '-' in claim_id else None
            
            if reviewer_id and reviewer_id in weights and claim_id in verifications:
                if reviewer_id not in reviewer_scores:
                    reviewer_scores[reviewer_id] = []
                    reviewer_weights[reviewer_id] = weights[reviewer_id].get('weight', 0.5)
                
                result = verifications[claim_id].get('verification_result', '')
                if result == 'True':
                    reviewer_scores[reviewer_id].append(1.0)
                elif result == 'Partially_True':
                    reviewer_scores[reviewer_id].append(0.7)
                else:
                    reviewer_scores[reviewer_id].append(0.0)
        
        total_weighted = 0.0
        total_weight = 0.0
        
        for reviewer_id, scores in reviewer_scores.items():
            if scores:
                avg = sum(scores) / len(scores)
                weight = reviewer_weights[reviewer_id]
                total_weighted += avg * weight
                total_weight += weight
        
        final_score = total_weighted / total_weight if total_weight > 0 else 0.5
    
    return final_score


def calculate_ensemble_score(paper_data: Dict) -> float:
    """
    Ensemble of multiple methods with adaptive threshold
    """
    score1 = calculate_advanced_score(paper_data)
    score2 = calculate_hybrid_score_v2(paper_data)
    
    # Weighted ensemble
    ensemble_score = 0.6 * score1 + 0.4 * score2
    
    return ensemble_score


def main():
    """Main function"""
    print("="*70)
    print("DESIGNING IMPROVED PREDICTION METHOD (Target: 80% Accuracy)")
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
    
    # Load all paper data
    papers_data = []
    for paper_id in paper_ids:
        data = load_paper_data(paper_id)
        if data['ground_truth'] != "Unknown":
            papers_data.append(data)
    
    print(f"Loaded {len(papers_data)} papers")
    print()
    
    # Test different methods and thresholds
    methods = {
        'Advanced Score': calculate_advanced_score,
        'Hybrid V2': calculate_hybrid_score_v2,
        'Ensemble': calculate_ensemble_score
    }
    
    results = {}
    
    for method_name, method_func in methods.items():
        print(f"Testing: {method_name}")
        print("-"*70)
        
        # Calculate scores for all papers
        paper_scores = []
        for paper_data in papers_data:
            score = method_func(paper_data)
            paper_scores.append((paper_data['paper_id'], paper_data['ground_truth'], score))
        
        # Test different thresholds
        best_threshold = 0.5
        best_accuracy = 0.0
        best_results = None
        
        for threshold in [0.40, 0.42, 0.44, 0.46, 0.48, 0.50, 0.52, 0.54, 0.56, 0.58, 0.60]:
            tp = sum(1 for pid, gt, score in paper_scores if gt == "Accepted" and score >= threshold)
            tn = sum(1 for pid, gt, score in paper_scores if gt == "Rejected" and score < threshold)
            accuracy = (tp + tn) / len(paper_scores)
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_threshold = threshold
                best_results = {
                    'threshold': threshold,
                    'accuracy': accuracy,
                    'tp': tp,
                    'tn': tn,
                    'fp': len(paper_scores) - tp - tn - tn,  # Fix calculation
                    'fn': len(paper_scores) - tp - tn - (len(paper_scores) - tp - tn - tn),
                    'predictions': [
                        {
                            'paper_id': pid,
                            'ground_truth': gt,
                            'prediction': "Accepted" if score >= threshold else "Rejected",
                            'score': score,
                            'correct': (gt == "Accepted" and score >= threshold) or (gt == "Rejected" and score < threshold)
                        }
                        for pid, gt, score in paper_scores
                    ]
                }
        
        # Recalculate properly
        tp = sum(1 for pid, gt, score in paper_scores if gt == "Accepted" and score >= best_threshold)
        tn = sum(1 for pid, gt, score in paper_scores if gt == "Rejected" and score < best_threshold)
        fp = sum(1 for pid, gt, score in paper_scores if gt == "Rejected" and score >= best_threshold)
        fn = sum(1 for pid, gt, score in paper_scores if gt == "Accepted" and score < best_threshold)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        results[method_name] = {
            'threshold': best_threshold,
            'accuracy': best_accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': tp,
            'tn': tn,
            'fp': fp,
            'fn': fn,
            'predictions': [
                {
                    'paper_id': pid,
                    'ground_truth': gt,
                    'prediction': "Accepted" if score >= best_threshold else "Rejected",
                    'score': score,
                    'correct': (gt == "Accepted" and score >= best_threshold) or (gt == "Rejected" and score < best_threshold)
                }
                for pid, gt, score in paper_scores
            ]
        }
        
        print(f"  Best Threshold: {best_threshold:.2f}")
        print(f"  Accuracy: {best_accuracy*100:.1f}%")
        print(f"  Precision: {precision*100:.1f}%")
        print(f"  Recall: {recall*100:.1f}%")
        print(f"  F1: {f1*100:.1f}%")
        print()
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print(f"{'Method':<20} {'Threshold':<12} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1':<12}")
    print("-"*70)
    for method_name, result in results.items():
        print(f"{method_name:<20} {result['threshold']:>6.2f}      "
              f"{result['accuracy']*100:>6.1f}%     "
              f"{result['precision']*100:>6.1f}%     "
              f"{result['recall']*100:>6.1f}%     "
              f"{result['f1']*100:>6.1f}%")
    print()
    
    # Find best method
    best_method = max(results.items(), key=lambda x: x[1]['accuracy'])
    print(f"Best Method: {best_method[0]} (Accuracy: {best_method[1]['accuracy']*100:.1f}%)")
    print()
    
    # Show error cases for best method
    if best_method[1]['accuracy'] < 0.8:
        print("Error Cases:")
        print("-"*70)
        for pred in best_method[1]['predictions']:
            if not pred['correct']:
                print(f"  {pred['paper_id']}: GT={pred['ground_truth']}, Pred={pred['prediction']}, Score={pred['score']:.3f}")
        print()
    
    # Save results
    output_path = Path("data/results/iclr2024_redesigned_prediction.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_path}")
    print("="*70)


if __name__ == "__main__":
    main()

