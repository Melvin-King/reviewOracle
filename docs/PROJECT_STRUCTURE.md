# ReviewOracle E-V-W Evaluation Stack

## Directory Structure

```
paperreview/
├── README.md                          
├── requirements.txt                  
├── config.yaml                    
│
├── data/                      
│   ├── raw/                           # Raw data
│   │   ├── papers/                    # Downloaded paper PDF
│   │   │   ├── paper_001.pdf
│   │   │   ├── paper_002.pdf
│   │   │   └── paper_003.pdf
│   │   └── reviews/                   # Downloaded review text
│   │       ├── paper_001_reviews.json
│   │       ├── paper_002_reviews.json
│   │       └── paper_003_reviews.json
│   ├── processed/                     # Processed data
│   │   ├── papers/                    # The parsed paper text
│   │   │   ├── paper_001.txt
│   │   │   ├── paper_002.txt
│   │   │   └── paper_003.txt
│   │   └── extracted/                 # Step 1
│   │       ├── paper_001_claims.json
│   │       ├── paper_002_claims.json
│   │       └── paper_003_claims.json
│   └── results/                       
│       ├── verifications/             # Step 2 Verification results
│       │   ├── paper_001_verified.json
│       │   ├── paper_002_verified.json
│       │   └── paper_003_verified.json
│       ├── weights/                   # Step 3 Weight calculation results
│       │   ├── paper_001_weights.json
│       │   ├── paper_002_weights.json
│       │   └── paper_003_weights.json
│       └── synthesis/                 # Step 4 Final Report
│           ├── paper_001_report.md
│           ├── paper_002_report.md
│           └── paper_003_report.md
│
├── src/          
│   ├── __init__.py
│   │
│   ├── data/                           # Data download and processing module
│   │   ├── __init__.py
│   │   ├── downloader.py              # Download papers and reviews from NeurIPS 2024
│   │   ├── pdf_parser.py               # PDF parsing tools
│   │   └── data_loader.py              # Data loading tool
│   │
│   ├── agents/                         # Agent implementation
│   │   ├── __init__.py
│   │   ├── extraction_agent.py        # Step 1: Structured extraction Agent
│   │   ├── verification_agent.py      # Step 2: Fact Verification Agent
│   │   ├── weighting_agent.py         # Step 3: Deviation Calculation and Weighted Agent
│   │   └── synthesis_agent.py         # Step 4: Synthetic Decision Agent
│   │
│   ├── utils/                   
│   │   ├── __init__.py
│   │   ├── llm_client.py               # LLM API Client Wrapper
│   │   ├── rag.py                      # RAG search enhancement generation tool
│   │   ├── text_processing.py         # Text processing tools
│   │   └── metrics.py                  # Tool functions for calculating indicators
│   │
│   └── pipeline.py                  
│
├── tests/                              # test files
│   ├── __init__.py
│   ├── test_extraction.py
│   ├── test_verification.py
│   └── test_weighting.py
│
└── scripts/                            # script files
    ├── download_data.py               
    ├── run_pipeline.py            
    └── visualize_results.py        
```
