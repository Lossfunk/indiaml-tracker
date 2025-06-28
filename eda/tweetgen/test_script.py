#!/usr/bin/env python3
"""
Test script for the tweet generator

This script creates a small test dataset and demonstrates the tweet generator functionality.
"""

import json
import os
import sys
from pathlib import Path

def create_test_data():
    """Create a small test dataset from the ICML 2025 data."""
    
    # Sample data based on the actual ICML 2025 structure
    test_papers = [
        {
            "paper_title": "NextCoder: Robust Adaptation of Code LMs to Diverse Code Edits",
            "paper_id": "3B6fF1PxYD",
            "pdf_url": "https://openreview.net/pdf/e4c45e8d4642143f7bff681474b7ce9634b0db2d.pdf",
            "author_list": [
                {
                    "name": "Tushar Aggarwal",
                    "openreview_id": "~Tushar_Aggarwal1",
                    "affiliation_name": "Microsoft",
                    "affiliation_domain": "microsoft.com",
                    "affiliation_country": "IN"
                },
                {
                    "name": "Swayam Singh",
                    "openreview_id": "~Swayam_Singh1",
                    "affiliation_name": "Microsoft",
                    "affiliation_domain": "microsoft.com",
                    "affiliation_country": "IN"
                },
                {
                    "name": "Abhijeet Awasthi",
                    "openreview_id": "~Abhijeet_Awasthi1",
                    "affiliation_name": "Microsoft",
                    "affiliation_domain": "microsoft.com",
                    "affiliation_country": "IN"
                }
            ],
            "top_author_from_india": True,
            "majority_authors_from_india": True,
            "paper_content": "This paper aims to improve code language models' ability to handle various code editing tasks. It introduces a novel synthetic data generation pipeline and a robust model adaptation algorithm, called SeleKT, to address the challenges of lacking high-quality fine-tuning data and potential loss of pre-trained abilities during adaptation."
        },
        {
            "paper_title": "Teaching Transformers Causal Reasoning through Axiomatic Training",
            "paper_id": "AhebPqDOMI",
            "pdf_url": "https://openreview.net/pdf/aac9925b5ab7b998cbccb8c1e5309f480692e75f.pdf",
            "author_list": [
                {
                    "name": "Aniket Vashishtha",
                    "openreview_id": "~Aniket_Vashishtha1",
                    "affiliation_name": "University of Illinois at Urbana-Champaign",
                    "affiliation_domain": "illinois.edu",
                    "affiliation_country": "US"
                },
                {
                    "name": "Abhinav Kumar",
                    "openreview_id": "~Abhinav_Kumar3",
                    "affiliation_name": "Massachusetts Institute of Technology",
                    "affiliation_domain": "mit.edu",
                    "affiliation_country": "US"
                }
            ],
            "top_author_from_india": False,
            "majority_authors_from_india": False,
            "paper_content": "This paper investigates whether large language models (LLMs) can learn causal reasoning by directly absorbing symbolic demonstrations of causal axioms, instead of relying on data. The authors specifically examine whether models trained on demonstrations of axioms, such as transitivity and d-separation, generalize to more complex causal scenarios."
        }
    ]
    
    return test_papers

def main():
    """Run the test."""
    
    print("🧪 Creating test dataset...")
    test_data = create_test_data()
    
    # Save test data
    test_file = "test_papers.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Test data saved to {test_file}")
    print(f"📊 Test dataset contains {len(test_data)} papers")
    
    print("\n" + "="*60)
    print("🚀 TO RUN THE TWEET GENERATOR:")
    print("="*60)
    print()
    print("1. Get your Exa API key from https://exa.ai")
    print()
    print("2. Install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print("3. Run the test:")
    print(f"   python tweet_generator.py {test_file} --exa-api-key YOUR_EXA_API_KEY")
    print()
    print("4. Or run with the full ICML 2025 dataset:")
    print("   python tweet_generator.py ../../ui/indiaml-tracker/public/tracker/icml-2025.json --exa-api-key YOUR_EXA_API_KEY")
    print()
    print("5. For testing with limited papers:")
    print("   python tweet_generator.py ../../ui/indiaml-tracker/public/tracker/icml-2025.json --exa-api-key YOUR_EXA_API_KEY --limit 5")
    print()
    print("="*60)
    print()
    
    # Show sample paper info
    print("📄 Sample papers in test dataset:")
    for i, paper in enumerate(test_data, 1):
        print(f"\n{i}. {paper['paper_title']}")
        print(f"   Authors: {len(paper['author_list'])}")
        print(f"   Content: {paper['paper_content'][:100]}...")

if __name__ == "__main__":
    main()
