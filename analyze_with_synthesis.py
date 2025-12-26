"""
Analyze prediction using Step 4 synthesis results
All outputs in English
"""

import sys
import io
import json
import re
from pathlib import Path
from typing import Dict, Optional

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


def parse_synthesis_report(report_path: Path) -> Optional[Dict]:
    """Parse synthesis report to extract scores and decision"""
    if not report_path.exists():
        return None
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    result = {
        'overall_decision': None,
        'average_score_10': None,
        'topic_scores': {}
    }
    
    # Extract overall decision
    decision_match = re.search(r'Overall Recommendation:\s*(ACCEPT|REJECT)', content, re.IGNORECASE)
    if decision_match:
        result['overall_decision'] = decision_match.group(1).upper()
    
    # Extract average score
    score_match = re.search(r'Average Topic Score.*?(\d+\.\d+)', content)
    if score_match:
        result['average_score_10'] = float(score_match.group(1))
    
    # Extract topic scores
    topic_pattern = r'###\s+(\w+).*?Score.*?(\d+\.\d+)'
    for match in re.finditer(topic_pattern, content, re.DOTALL):
        topic = match.group(1)
        score = float(match.group(2))
        result['topic_scores'][topic] = score
    
    return result


def main():
    """Analyze prediction using synthesis results"""
    print("="*70)
    print("PREDICTION USING SYNTHESIS RESULTS")
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
    
    # Check which papers have synthesis reports
    papers_with_synthesis = []
    papers_without_synthesis = []
    
    for paper_id in paper_ids:
        ground_truth = get_ground_truth_status(paper_id)
        if ground_truth == "Unknown":
            continue
        
        report_path = Path(f"data/results/synthesis/{paper_id}_report.md")
        synthesis_data = parse_synthesis_report(report_path)
        
        if synthesis_data and synthesis_data['overall_decision']:
            papers_with_synthesis.append({
                'paper_id': paper_id,
                'ground_truth': ground_truth,
                'synthesis': synthesis_data
            })
        else:
            papers_without_synthesis.append(paper_id)
    
    print(f"Papers with synthesis reports: {len(papers_with_synthesis)}")
    print(f"Papers without synthesis reports: {len(papers_without_synthesis)}")
    if papers_without_synthesis:
        print(f"  Missing: {', '.join(papers_without_synthesis)}")
    print()
    
    if not papers_with_synthesis:
        print("No synthesis reports found. Please run Step 4 first.")
        return
    
    # Analyze predictions
    print("PREDICTION ANALYSIS")
    print("-"*70)
    
    correct = 0
    total = len(papers_with_synthesis)
    
    for paper in papers_with_synthesis:
        prediction = paper['synthesis']['overall_decision']
        ground_truth = paper['ground_truth']
        is_correct = prediction == ground_truth
        
        if is_correct:
            correct += 1
        
        status = "✓" if is_correct else "✗"
        avg_score = paper['synthesis'].get('average_score_10', 'N/A')
        print(f"{status} {paper['paper_id']}: {ground_truth} -> {prediction} (avg score: {avg_score})")
    
    accuracy = correct / total if total > 0 else 0
    print(f"\nAccuracy: {accuracy*100:.1f}% ({correct}/{total})")
    
    # Compare with verification-based method
    print("\n" + "="*70)
    print("COMPARISON WITH VERIFICATION-BASED METHOD")
    print("-"*70)
    
    # Load verification-based predictions
    accuracy_path = Path("data/results/iclr2024_prediction_accuracy.json")
    if accuracy_path.exists():
        with open(accuracy_path, 'r', encoding='utf-8') as f:
            accuracy_data = json.load(f)
        
        method2_results = accuracy_data.get('Method 2: Weighted Verification Score', {})
        method2_accuracy = method2_results.get('metrics', {}).get('accuracy', 0)
        
        print(f"Verification-based Method: {method2_accuracy*100:.1f}%")
        print(f"Synthesis-based Method: {accuracy*100:.1f}%")
        
        if accuracy > method2_accuracy:
            print(f"\n✓ Synthesis method is better by {(accuracy - method2_accuracy)*100:.1f}%")
        elif accuracy < method2_accuracy:
            print(f"\n✗ Synthesis method is worse by {(method2_accuracy - accuracy)*100:.1f}%")
        else:
            print(f"\n= Both methods have the same accuracy")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()

