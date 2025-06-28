#!/usr/bin/env python3
"""
Tweet Thread Generator for Research Papers

This script processes research papers from JSON files, finds Twitter profiles for authors
using the Exa API, generates tweet threads, and creates markdown output.

Usage:
    python tweet_generator.py input.json --exa-api-key YOUR_API_KEY --output tweets.md

Requirements:
    pip install exa_py pillow cairosvg reportlab
"""

import json
import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
import re
from datetime import datetime
import exa_py

# Import card generation functionality
from card import generate_svg, convert_svg_to_image, clean_filename

class ExaAPIClient:
    """Client for interacting with Exa API to find Twitter profiles using exa_py AsyncExa."""
    
    def __init__(self, api_key: str):
        self.exa = exa_py.AsyncExa(api_key)
    
    async def search_twitter_profile(self, author_name: str, paper_title: str = "", affiliation: str = "") -> Optional[str]:
        """Search for Twitter profile of an author using Exa API."""
        try:
            # Construct search query for finding Twitter profile
            query = f"What is the Twitter handle or X.com profile for {author_name}"
            if paper_title:
                query += f", author of the paper '{paper_title}'"
            if affiliation:
                query += f" from {affiliation}"
            query += "? Please provide the Twitter/X username or profile URL."
            
            # Use exa.answer API to find Twitter profile
            response = await self.exa.answer(query, text=True)
            
            if response and hasattr(response, 'answer') and response.answer:
                answer_text = response.answer
                
                # Extract Twitter handle from the answer
                twitter_handle = self._extract_twitter_handle(answer_text)
                return twitter_handle
                    
        except Exception as e:
            print(f"Exception searching for {author_name}: {str(e)}")
        
        return None
    
    def _extract_twitter_handle(self, text: str) -> Optional[str]:
        """Extract Twitter handle or URL from text response."""
        # Look for @username pattern

        print("Exa Answer ---",text)
        handle_match = re.search(r'@([a-zA-Z0-9_]+)', text)
        if handle_match:
            return f"@{handle_match.group(1)}"
        
        # Look for twitter.com or x.com URLs
        url_match = re.search(r'(?:https?://)?(?:www\.)?(?:twitter\.com/|x\.com/)([^/\s]+)', text)
        if url_match:
            username = url_match.group(1)
            return f"@{username}"
        
        # Look for just the username mentioned
        username_match = re.search(r'(?:username|handle|profile).*?([a-zA-Z0-9_]{3,15})', text, re.IGNORECASE)
        if username_match:
            return f"@{username_match.group(1)}"
        
        return None
    
    async def get_answer(self, query: str) -> Optional[str]:
        """Get an answer from Exa API for a specific query."""
        try:
            response = await self.exa.answer(query, text=True)
            if response and hasattr(response, 'answer'):
                return response.answer
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

async def find_twitter_profiles(authors: List[Dict[str, str]], exa_client: ExaAPIClient, paper_title: str = "") -> Dict[str, str]:
    """Find Twitter profiles for all authors."""
    twitter_profiles = {}
    
    print(f"Searching for Twitter profiles for {len(authors)} authors...")
    
    for i, author in enumerate(authors):
        print(f"  [{i+1}/{len(authors)}] Searching for {author['name']}...")
        
        twitter_url = await exa_client.search_twitter_profile(
            author['name'], 
            paper_title,
            author.get('affiliation', '')
        )
        
        if twitter_url:
            # Check if it's already a handle format
            if twitter_url.startswith('@'):
                twitter_profiles[author['name']] = twitter_url
                print(f"    Found: {twitter_url}")
            else:
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
        await asyncio.sleep(1)
    
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
    
    # Determine conference details
    conference_title = "ICML"
    conference_year = "2025"
    presentation_type = paper.get("presentation_type", "poster")  # Default to poster if not specified
    
    # Check if any authors are from India
    has_indian_authors = any(author.get("country") == "IN" for author in authors)
    india_text = " from India" if has_indian_authors else ""
    
    # Create author list with Twitter mentions and LinkedIn placeholders
    author_lines = []
    for author in authors:
        name = author["name"]
        twitter_mention = twitter_profiles.get(name, "")
        linkedin = ""  # Placeholder for LinkedIn - could be enhanced later
        
        author_line = name
        if twitter_mention:
            author_line += f" {twitter_mention}"
        if linkedin:
            author_line += f" {linkedin}"
        
        author_lines.append(author_line)
    
    authors_text = "\n".join(author_lines)
    
    # Generate tweet in the requested format
    tweet_thread = f"""
## {title}

**Tweet:**
{conference_title} {conference_year} {presentation_type} paper{india_text}

{content if content else title}

Authors
{authors_text}

📖 Read the full paper: {pdf_url}
🖼️ Paper card: {card_filename}

#MachineLearning #AI #Research #IndiaML
"""
    
    return tweet_thread.strip()

async def process_papers(input_file: str, exa_api_key: str, output_dir: str, output_file: str):
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
        twitter_profiles = await find_twitter_profiles(authors, exa_client, paper['paper_title'])
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
        asyncio.run(process_papers(input_file, args.exa_api_key, args.output_dir, args.output_file))
    finally:
        # Clean up temporary file
        if args.limit and os.path.exists("temp_limited_papers.json"):
            os.remove("temp_limited_papers.json")

if __name__ == "__main__":
    main()
