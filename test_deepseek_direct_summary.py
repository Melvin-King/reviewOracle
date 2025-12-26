"""
Test DeepSeek direct summary of reviews to get accept/reject decision
Compare accuracy with ground truth
All outputs in English
"""

import sys
import io
import json
import yaml
import time
from pathlib import Path
from typing import Dict, List, Tuple
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


def summarize_reviews_with_deepseek(reviews: List[Dict], llm_client: LLMClient) -> str:
    """
    Use DeepSeek to summarize reviews and get accept/reject decision
    
    Args:
        reviews: List of review dictionaries
        llm_client: LLMClient instance
        
    Returns:
        Decision: "Accept" or "Reject"
    """
    # Combine all reviews
    review_texts = []
    for i, review in enumerate(reviews, 1):
        review_content = review.get('content', {})
        review_text = review_content.get('review', '')
        rating = review_content.get('rating', 'N/A')
        
        review_texts.append(f"Review {i} (Rating: {rating}):\n{review_text}\n")
    
    combined_reviews = "\n".join(review_texts)
    
    # Create prompt
    system_prompt = """You are an expert academic reviewer. Your task is to analyze peer reviews and determine whether a paper should be accepted or rejected based on the reviewers' feedback.

Consider the following factors:
1. Overall ratings and sentiment
2. Strengths and weaknesses mentioned
3. Consensus among reviewers
4. Severity of concerns raised
5. Potential for improvement

Respond with ONLY one word: "Accept" or "Reject". Do not provide any explanation or additional text."""

    user_prompt = f"""Based on the following peer reviews, determine if the paper should be ACCEPT or REJECT:

{combined_reviews}

Decision (Accept or Reject):"""

    try:
        response = llm_client.call(user_prompt, system_prompt=system_prompt, max_tokens=50)
        
        # Extract decision from response
        response = response.strip().upper()
        if "ACCEPT" in response:
            return "Accepted"
        elif "REJECT" in response:
            return "Rejected"
        else:
            # Try to parse more carefully
            response_lower = response.lower()
            if "accept" in response_lower:
                return "Accepted"
            elif "reject" in response_lower:
                return "Rejected"
            else:
                # Default based on first word
                first_word = response.split()[0].upper() if response.split() else ""
                if first_word == "ACCEPT":
                    return "Accepted"
                elif first_word == "REJECT":
                    return "Rejected"
                else:
                    print(f"Warning: Could not parse response: {response}")
                    return "Unknown"
    except Exception as e:
        print(f"Error calling DeepSeek: {e}")
        return "Unknown"


def main():
    """Main function"""
    print("="*70)
    print("DEEPSEEK DIRECT SUMMARY TEST")
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
    
    print(f"Found {len(paper_ids)} papers")
    print()
    
    # Process each paper
    results = []
    for i, paper_id in enumerate(paper_ids, 1):
        print(f"[{i}/{len(paper_ids)}] Processing: {paper_id}")
        
        ground_truth = get_ground_truth_status(paper_id)
        if ground_truth == "Unknown":
            print(f"  Skipping: Unknown ground truth")
            continue
        
        # Load reviews
        reviews_path = Path(f"data/raw/iclr2024/reviews/{paper_id}_reviews.json")
        if not reviews_path.exists():
            print(f"  Skipping: No reviews found")
            continue
        
        with open(reviews_path, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        
        if not reviews:
            print(f"  Skipping: Empty reviews")
            continue
        
        # Get prediction from DeepSeek
        print(f"  Calling DeepSeek...")
        prediction = summarize_reviews_with_deepseek(reviews, llm_client)
        
        is_correct = prediction == ground_truth
        
        results.append({
            'paper_id': paper_id,
            'ground_truth': ground_truth,
            'prediction': prediction,
            'correct': is_correct
        })
        
        print(f"  Ground Truth: {ground_truth}")
        print(f"  Prediction: {prediction}")
        print(f"  Correct: {is_correct}")
        print()
        
        # Rate limiting
        time.sleep(1)
    
    # Calculate metrics
    print("="*70)
    print("RESULTS")
    print("="*70)
    print()
    
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
    
    print(f"Total Papers: {total}")
    print(f"Correct Predictions: {correct}")
    print(f"Accuracy: {accuracy*100:.1f}%")
    print()
    print("Confusion Matrix:")
    print(f"  True Positives (TP): {tp}")
    print(f"  True Negatives (TN): {tn}")
    print(f"  False Positives (FP): {fp}")
    print(f"  False Negatives (FN): {fn}")
    print()
    print("Metrics:")
    print(f"  Precision: {precision*100:.1f}%")
    print(f"  Recall: {recall*100:.1f}%")
    print(f"  F1 Score: {f1*100:.1f}%")
    print()
    
    # Show per-paper results
    print("Per-Paper Results:")
    print("-"*70)
    for r in results:
        status = "✓" if r['correct'] else "✗"
        print(f"{status} {r['paper_id']}: GT={r['ground_truth']}, Pred={r['prediction']}")
    print()
    
    # Save results
    output_path = Path("data/results/deepseek_direct_summary_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
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
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_path}")
    print("="*70)


if __name__ == "__main__":
    main()

