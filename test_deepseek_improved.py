"""
Test improved DeepSeek prompt with more context
All outputs in English
"""

import sys
import io
import json
import yaml
import time
from pathlib import Path
from typing import Dict, List
from src.utils.llm_client import LLMClient

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


def load_config() -> Dict:
    """Load configuration from config.yaml"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        raise FileNotFoundError("config.yaml not found")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def summarize_reviews_improved(reviews: List[Dict], llm_client: LLMClient, method: str = "default") -> str:
    """
    Use DeepSeek to summarize reviews with improved prompts
    
    Args:
        reviews: List of review dictionaries
        llm_client: LLMClient instance
        method: "default", "detailed", or "rating_focused"
        
    Returns:
        Decision: "Accept" or "Reject"
    """
    # Combine all reviews with ratings
    review_texts = []
    ratings = []
    
    for i, review in enumerate(reviews, 1):
        review_content = review.get('content', {})
        review_text = review_content.get('review', '')
        rating = review_content.get('rating', 'N/A')
        
        if rating != 'N/A':
            try:
                rating_num = float(rating)
                ratings.append(rating_num)
            except:
                pass
        
        review_texts.append(f"=== Review {i} (Rating: {rating}) ===\n{review_text}\n")
    
    combined_reviews = "\n".join(review_texts)
    
    # Calculate average rating
    avg_rating = sum(ratings) / len(ratings) if ratings else None
    
    if method == "rating_focused":
        # Method 1: Focus on ratings
        system_prompt = """You are an expert academic reviewer analyzing peer reviews for a conference paper.

Your task is to determine if the paper should be ACCEPTED or REJECTED based on:
1. Reviewer ratings (typically 1-10 scale, where 6+ suggests acceptance)
2. Overall sentiment and consensus
3. Severity of concerns

Respond with ONLY "Accept" or "Reject"."""

        user_prompt = f"""Reviewer Ratings: {ratings if ratings else 'N/A'}
Average Rating: {avg_rating:.2f if avg_rating else 'N/A'}

Reviews:
{combined_reviews}

Decision:"""
    
    elif method == "detailed":
        # Method 2: Detailed analysis
        system_prompt = """You are an expert academic reviewer. Analyze peer reviews and determine if a paper should be ACCEPTED or REJECTED.

Consider:
1. Ratings: Papers with average rating >= 6.5 are typically accepted
2. Consensus: Agreement among reviewers
3. Strengths vs Weaknesses: Balance of positive and negative feedback
4. Severity: Critical flaws vs minor issues
5. Potential: Can issues be addressed?

Respond with ONLY "Accept" or "Reject"."""

        user_prompt = f"""Analyze these peer reviews:

Ratings: {ratings if ratings else 'N/A'} (Average: {avg_rating:.2f if avg_rating else 'N/A'})

{combined_reviews}

Based on ratings, consensus, and review content, should this paper be ACCEPTED or REJECTED?
Decision:"""
    
    else:
        # Default method: Simple but clear
        system_prompt = """You are an expert academic reviewer. Based on peer reviews, determine if a paper should be ACCEPTED or REJECTED.

Key indicators for ACCEPTANCE:
- Average rating >= 6.5
- Mostly positive feedback
- Minor concerns that can be addressed

Key indicators for REJECTION:
- Average rating < 6.5
- Major flaws or limitations
- Fundamental issues

Respond with ONLY "Accept" or "Reject"."""

        user_prompt = f"""Reviews with ratings: {ratings if ratings else 'N/A'} (Avg: {avg_rating:.2f if avg_rating else 'N/A'})

{combined_reviews}

Decision (Accept or Reject):"""

    try:
        response = llm_client.call(user_prompt, system_prompt=system_prompt, max_tokens=50)
        
        # Extract decision
        response = response.strip().upper()
        if "ACCEPT" in response:
            return "Accepted"
        elif "REJECT" in response:
            return "Rejected"
        else:
            # Try parsing
            response_lower = response.lower()
            if "accept" in response_lower:
                return "Accepted"
            elif "reject" in response_lower:
                return "Rejected"
            else:
                # Use rating as fallback
                if avg_rating and avg_rating >= 6.5:
                    return "Accepted"
                elif avg_rating and avg_rating < 6.5:
                    return "Rejected"
                else:
                    print(f"Warning: Could not parse response: {response}")
                    return "Unknown"
    except Exception as e:
        print(f"Error calling DeepSeek: {e}")
        # Fallback to rating-based decision
        if avg_rating and avg_rating >= 6.5:
            return "Accepted"
        elif avg_rating and avg_rating < 6.5:
            return "Rejected"
        return "Unknown"


def main():
    """Main function"""
    print("="*70)
    print("DEEPSEEK IMPROVED PROMPT TEST")
    print("="*70)
    print()
    
    # Load config
    config = load_config()
    llm_config = config.get('llm', {})
    
    # Initialize LLM client
    llm_client = LLMClient(
        provider=llm_config.get('provider', 'deepseek'),
        api_key=llm_config.get('api_key'),
        model=llm_config.get('model', 'deepseek-chat'),
        temperature=llm_config.get('temperature', 0.3)
    )
    
    # Find all ICLR papers
    accepted_dir = Path("data/raw/iclr2024/papers/accepted")
    rejected_dir = Path("data/raw/iclr2024/papers/rejected")
    
    paper_ids = []
    if accepted_dir.exists():
        paper_ids.extend([f.stem for f in accepted_dir.glob("*.pdf")])
    if rejected_dir.exists():
        paper_ids.extend([f.stem for f in rejected_dir.glob("*.pdf")])
    
    # Test different methods
    methods = ["default", "detailed", "rating_focused"]
    all_results = {}
    
    for method in methods:
        print(f"\n{'='*70}")
        print(f"Testing Method: {method}")
        print('='*70)
        print()
        
        results = []
        for i, paper_id in enumerate(paper_ids, 1):
            print(f"[{i}/{len(paper_ids)}] {paper_id}", end=" ... ")
            
            ground_truth = get_ground_truth_status(paper_id)
            if ground_truth == "Unknown":
                print("Skipped")
                continue
            
            reviews_path = Path(f"data/raw/iclr2024/reviews/{paper_id}_reviews.json")
            if not reviews_path.exists():
                print("Skipped (no reviews)")
                continue
            
            with open(reviews_path, 'r', encoding='utf-8') as f:
                reviews = json.load(f)
            
            if not reviews:
                print("Skipped (empty)")
                continue
            
            prediction = summarize_reviews_improved(reviews, llm_client, method=method)
            is_correct = prediction == ground_truth
            
            results.append({
                'paper_id': paper_id,
                'ground_truth': ground_truth,
                'prediction': prediction,
                'correct': is_correct
            })
            
            status = "✓" if is_correct else "✗"
            print(f"{status} {prediction}")
            
            time.sleep(1)
        
        # Calculate metrics
        total = len(results)
        correct = sum(1 for r in results if r['correct'])
        accuracy = correct / total if total > 0 else 0
        
        tp = sum(1 for r in results if r['ground_truth'] == "Accepted" and r['prediction'] == "Accepted")
        tn = sum(1 for r in results if r['ground_truth'] == "Rejected" and r['prediction'] == "Rejected")
        fp = sum(1 for r in results if r['ground_truth'] == "Rejected" and r['prediction'] == "Accepted")
        fn = sum(1 for r in results if r['ground_truth'] == "Accepted" and r['prediction'] == "Rejected")
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        all_results[method] = {
            'metrics': {
                'total': total,
                'correct': correct,
                'accuracy': accuracy,
                'tp': tp,
                'tn': tn,
                'fp': fp,
                'fn': fn,
                'precision': precision,
                'recall': recall,
                'f1': f1
            },
            'paper_results': results
        }
        
        print(f"\nMethod {method} Results:")
        print(f"  Accuracy: {accuracy*100:.1f}%")
        print(f"  Precision: {precision*100:.1f}%")
        print(f"  Recall: {recall*100:.1f}%")
        print(f"  F1: {f1*100:.1f}%")
    
    # Summary comparison
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    print()
    print(f"{'Method':<20} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1':<12}")
    print("-"*70)
    for method, data in all_results.items():
        m = data['metrics']
        print(f"{method:<20} {m['accuracy']*100:>6.1f}%     {m['precision']*100:>6.1f}%     {m['recall']*100:>6.1f}%     {m['f1']*100:>6.1f}%")
    print()
    
    # Save results
    output_path = Path("data/results/deepseek_improved_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_path}")
    print("="*70)


if __name__ == "__main__":
    main()

