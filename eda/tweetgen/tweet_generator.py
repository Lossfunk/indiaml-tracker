#!/usr/bin/env python3
"""
Tweet Thread Generator for Research Papers

This script processes research papers from JSON files, finds Twitter profiles for authors
using the Exa API, generates tweet threads, and creates markdown output.

Usage:
    python tweet_generator.py input.json --exa-api-key YOUR_API_KEY --output tweets.md

Requirements:
    pip install requests pillow cairosvg reportlab
"""

import json
import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import time
import re
from datetime import datetime

# Import card generation functionality
from card import generate_svg, convert_svg_to_image, clean_filename

class ExaAPIClient:
    """Client for interacting with Exa API to find Twitter profiles."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.exa.ai"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def search_twitter_profile(self, author_name: str, affiliation: str = "") -> Optional[str]:
        """Search for Twitter profile of an author using Exa API."""
        try:
            # Construct search query
            query = f"{author_name} Twitter profile"
            if affiliation:
                query += f" {affiliation}"
            
            # Add site restriction to Twitter
            query += " site:twitter.com OR site:x.com"
            
            payload = {
                "query": query,
                "type": "neural",
                "useAutoprompt": True,
                "numResults": 3,
                "includeDomains": ["twitter.com", "x.com"]
            }
            
            response = requests.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                if results.get("results"):
                    # Return the first result's URL
                    return results["results"][0].get("url")
            else:
                print(f"Error searching for {author_name}: {response.status_code}")
                
        except Exception as e:
            print(f"Exception searching for {author_name}: {str(e)}")
        
        return None
    
    def get_answer(self, query: str) -> Optional[str]:
        """Get an answer from Exa API for a specific query."""
        try:
            payload = {
                "query": query,
                "useAutoprompt": True,
                "numResults": 5,
                "type": "neural"
            }
            
            response = requests.post(
                f"{self.base_url}/answer",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("answer", "")
            else:
                print(f"Error getting answer: {response.status_code}")
                
        except Exception as e:
            print(f"Exception getting answer: {str(e)}")
        
        return None

def extract_authors_from_paper(paper: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract author information from paper data."""
    authors = []
    
    for author_data in paper.get("author_list", []):
        name = author_data.get("name", "").strip()
        if not name:
            # Try to extract name from openreview_id if name is empty
            openreview_id = author_data.get("openreview_id", "")
            if openreview_id.startswith("~"):
                # Convert ~Name_Surname1 to Name Surname
                name = openreview_id[1:].replace("_", " ").split("1")[0]
        
        if name:
            affiliation = author_data.get("affiliation_name", "")
            country = author_data.get("affiliation_country", "")
            
            authors.append({
                "name": name,
                "affiliation": affiliation,
                "country": country
            })
    
    return authors

def get_country_flag(country_code: str) -> str:
    """Convert country code to emoji flag."""
    flag_map = {
        "IN": "🇮🇳", "US": "🇺🇸", "GB": "🇬🇧", "CA": "🇨🇦", "DE": "🇩🇪",
        "JP": "🇯🇵", "FR": "🇫🇷", "AU": "🇦🇺", "CN": "🇨🇳", "KR": "🇰🇷",
        "BR": "🇧🇷", "IT": "🇮🇹", "ES": "🇪🇸", "NL": "🇳🇱", "SE": "🇸🇪",
        "CH": "🇨🇭", "AT": "🇦🇹", "BE": "🇧🇪", "DK": "🇩🇰", "FI": "🇫🇮",
        "NO": "🇳🇴", "PL": "🇵🇱", "RU": "🇷🇺", "IL": "🇮🇱", "SG": "🇸🇬",
        "HK": "🇭🇰", "TW": "🇹🇼", "TH": "🇹🇭", "MX": "🇲🇽", "AR": "🇦🇷",
        "ZA": "🇿🇦", "EG": "🇪🇬", "NG": "🇳🇬", "KE": "🇰🇪", "GH": "🇬🇭"
    }
    return flag_map.get(country_code, "🌍")

def find_twitter_profiles(authors: List[Dict[str, str]], exa_client: ExaAPIClient) -> Dict[str, str]:
    """Find Twitter profiles for all authors."""
    twitter_profiles = {}
    
    print(f"Searching for Twitter profiles for {len(authors)} authors...")
    
    for i, author in enumerate(authors):
        print(f"  [{i+1}/{len(authors)}] Searching for {author['name']}...")
        
        twitter_url = exa_client.search_twitter_profile(
            author['name'], 
            author.get('affiliation', '')
        )
        
        if twitter_url:
            # Extract username from URL
            username_match = re.search(r'(?:twitter\.com/|x\.com/)([^/?]+)', twitter_url)
            if username_match:
                username = username_match.group(1)
                twitter_profiles[author['name']] = f"@{username}"
                print(f"    Found: @{username}")
            else:
                twitter_profiles[author['name']] = twitter_url
                print(f"    Found: {twitter_url}")
        else:
            print(f"    Not found")
        
        # Rate limiting - be respectful to the API
        time.sleep(1)
    
    return twitter_profiles

def generate_card_for_paper(paper: Dict[str, Any], output_dir: Path, paper_index: int) -> str:
    """Generate a card image for the paper and return the filename."""
    
    # Extract authors and convert to card format
    authors = extract_authors_from_paper(paper)
    card_authors = []
    
    # No longer limit to 8 authors - let the layout engine handle it
    for author in authors:
        card_authors.append({
            "name": author["name"],
            "flag": get_country_flag(author["country"])
        })
    
    # Prepare paper data for card generation
    card_data = {
        "title": paper["paper_title"],
        "authors": card_authors,
        "conference": "ICML 2025",
        "presentation_type": "Research Paper"
    }
    
    # Generate SVG
    svg_content = generate_svg(card_data)
    
    # Create filename
    safe_title = clean_filename(paper["paper_title"][:50])
    base_filename = f"paper_{paper_index:03d}_{safe_title}"
    
    # Save as PNG
    image_path = output_dir / f"{base_filename}.png"
    convert_svg_to_image(svg_content, str(image_path), "png")
    
    return image_path.name

def generate_tweet_thread(paper: Dict[str, Any], twitter_profiles: Dict[str, str], card_filename: str) -> str:
    """Generate a tweet thread for a paper."""
    
    title = paper["paper_title"]
    authors = extract_authors_from_paper(paper)
    content = paper.get("paper_content", "")
    pdf_url = paper.get("pdf_url", "")
    
    # Create author mentions
    author_mentions = []
    for author in authors:
        name = author["name"]
        if name in twitter_profiles:
            author_mentions.append(twitter_profiles[name])
        else:
            author_mentions.append(name)
    
    # Limit author mentions to avoid tweet length issues
    if len(author_mentions) > 6:
        displayed_authors = author_mentions[:6]
        displayed_authors.append(f"and {len(author_mentions) - 6} others")
    else:
        displayed_authors = author_mentions
    
    authors_text = ", ".join(displayed_authors)
    
    # Generate tweet thread
    tweet_thread = f"""
## {title}

**Tweet 1/3** 🧵
📄 New paper at #ICML2025: "{title}"

{content[:200]}{'...' if len(content) > 200 else ''}

🧵 Thread below 👇

**Tweet 2/3**
👥 Authors: {authors_text}

🔬 This work explores {content[:150]}{'...' if len(content) > 150 else ''}

**Tweet 3/3**
📊 Key insights from this research:
{content[150:300] if len(content) > 150 else content}{'...' if len(content) > 300 else ''}

📖 Read the full paper: {pdf_url}
🖼️ Paper card: {card_filename}

#MachineLearning #AI #Research #IndiaML
"""
    
    return tweet_thread.strip()

def process_papers(input_file: str, exa_api_key: str, output_dir: str, output_file: str):
    """Main processing function."""
    
    # Load papers data
    print(f"Loading papers from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        papers_data = json.load(f)
    
    if not isinstance(papers_data, list):
        raise ValueError("Expected JSON file to contain a list of papers")
    
    print(f"Found {len(papers_data)} papers")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize Exa API client
    exa_client = ExaAPIClient(exa_api_key)
    
    # Process each paper
    all_tweets = []
    
    for i, paper in enumerate(papers_data):
        print(f"\n=== Processing Paper {i+1}/{len(papers_data)} ===")
        print(f"Title: {paper['paper_title'][:80]}...")
        
        # Extract authors
        authors = extract_authors_from_paper(paper)
        print(f"Authors: {len(authors)} found")
        
        # Find Twitter profiles
        twitter_profiles = find_twitter_profiles(authors, exa_client)
        print(f"Twitter profiles found: {len(twitter_profiles)}")
        
        # Generate card
        print("Generating paper card...")
        card_filename = generate_card_for_paper(paper, output_path, i + 1)
        print(f"Card saved: {card_filename}")
        
        # Generate tweet thread
        print("Generating tweet thread...")
        tweet_thread = generate_tweet_thread(paper, twitter_profiles, card_filename)
        
        all_tweets.append({
            "paper_index": i + 1,
            "title": paper["paper_title"],
            "tweet_thread": tweet_thread,
            "card_filename": card_filename,
            "twitter_profiles": twitter_profiles
        })
        
        print("✅ Paper processed successfully")
    
    # Generate markdown output
    print(f"\nGenerating markdown output: {output_file}")
    generate_markdown_output(all_tweets, output_file)
    
    print(f"\n🎉 All done! Generated {len(all_tweets)} tweet threads")
    print(f"📁 Output directory: {output_dir}")
    print(f"📄 Markdown file: {output_file}")

def generate_markdown_output(all_tweets: List[Dict], output_file: str):
    """Generate markdown file with all tweet threads."""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# ICML 2025 Tweet Threads\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total papers: {len(all_tweets)}\n\n")
        f.write("---\n\n")
        
        for tweet_data in all_tweets:
            f.write(f"## Paper {tweet_data['paper_index']}: {tweet_data['title']}\n\n")
            f.write(f"**Card Image:** `{tweet_data['card_filename']}`\n\n")
            
            if tweet_data['twitter_profiles']:
                f.write("**Twitter Profiles Found:**\n")
                for name, handle in tweet_data['twitter_profiles'].items():
                    f.write(f"- {name}: {handle}\n")
                f.write("\n")
            
            f.write("**Tweet Thread:**\n\n")
            f.write(tweet_data['tweet_thread'])
            f.write("\n\n---\n\n")

def main():
    parser = argparse.ArgumentParser(description='Generate tweet threads for research papers')
    parser.add_argument('input_json', help='Input JSON file with paper data')
    parser.add_argument('--exa-api-key', required=True, help='Exa API key')
    parser.add_argument('--output-dir', default='tweet_output/', help='Output directory for cards (default: tweet_output/)')
    parser.add_argument('--output-file', default='tweets.md', help='Output markdown file (default: tweets.md)')
    parser.add_argument('--limit', type=int, help='Limit number of papers to process (for testing)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.input_json):
        print(f"Error: Input file {args.input_json} not found")
        sys.exit(1)
    
    if not args.exa_api_key:
        print("Error: Exa API key is required")
        sys.exit(1)
    
    # Load and optionally limit papers
    with open(args.input_json, 'r', encoding='utf-8') as f:
        papers_data = json.load(f)
    
    if args.limit:
        papers_data = papers_data[:args.limit]
        print(f"Limited to first {args.limit} papers for testing")
    
    # Save limited data to temporary file if needed
    if args.limit:
        temp_file = "temp_limited_papers.json"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(papers_data, f, indent=2)
        input_file = temp_file
    else:
        input_file = args.input_json
    
    try:
        process_papers(input_file, args.exa_api_key, args.output_dir, args.output_file)
    finally:
        # Clean up temporary file
        if args.limit and os.path.exists("temp_limited_papers.json"):
            os.remove("temp_limited_papers.json")

if __name__ == "__main__":
    main()
