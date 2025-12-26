from pathlib import Path

rejected_dir = Path('data/raw/iclr2024/papers/rejected')
accepted_dir = Path('data/raw/iclr2024/papers/accepted')
reviews_dir = Path('data/raw/iclr2024/reviews')

rejected_pdfs = list(rejected_dir.glob('*.pdf')) if rejected_dir.exists() else []
accepted_pdfs = list(accepted_dir.glob('*.pdf')) if accepted_dir.exists() else []
reviews = list(reviews_dir.glob('*_reviews.json')) if reviews_dir.exists() else []

print(f"Rejected PDFs: {len(rejected_pdfs)}")
for pdf in rejected_pdfs[:5]:
    print(f"  - {pdf.name}")

print(f"\nAccepted PDFs: {len(accepted_pdfs)}")
for pdf in accepted_pdfs[:5]:
    print(f"  - {pdf.name}")

print(f"\nReviews: {len(reviews)}")
for review in reviews[:10]:
    print(f"  - {review.name}")

