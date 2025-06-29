#!/usr/bin/env python3
"""
Integrated Research Paper Card Generator with Twitter Handle Finder

Generates social media cards for research papers and optionally finds Twitter handles for authors.
Uses HTML + CSS templates with Jinja2, converts to various image formats using Playwright, and creates a merged PDF.

Usage:
    # Generate cards only
    python tweet_generator.py input.json --format png --output cards/
    
    # Find Twitter handles first, then generate cards
    python tweet_generator.py input.json --find-twitter --format png --output cards/
    
    # Update existing data with Twitter handles only
    python tweet_generator.py input.json --find-twitter-only --output updated.json
    
    # Use custom template and branding
    python tweet_generator.py input.json --template custom_template.html --brand-text "My Conference"
    
    # Override conference and presentation type
    python tweet_generator.py input.json --conference "NeurIPS 2025" --presentation-type "Poster"
    
Requirements:
    pip install playwright pillow reportlab openai python-dotenv jinja2
    playwright install chromium
"""

import json
import argparse
import os
import asyncio
from pathlib import Path
import re
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import io
import base64
from openai import OpenAI
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

# Initialize OpenAI client for Twitter handle finding
try:
    client = OpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", os.environ.get("OPENAI_API_KEY")),
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )
except Exception:
    client = None

class TwitterHandleFinder:
    def __init__(self, max_concurrent: int = 3, timeout: int = 30000):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.processed_urls = set()
        self.stats = {
            'total_authors': 0,
            'handles_found': 0,
            'no_homepage': 0,
            'errors': 0,
            'multiple_handles': 0
        }

    def get_most_relevant_twitter_link_via_llm(self, author_name: str, paper_title: str, potential_links: List[str]) -> str:
        """Use LLM to select the most relevant Twitter/X profile from multiple options."""
        if not client:
            return potential_links[0] if potential_links else ""
            
        prompt = (
            f"From the following Twitter/X URLs found on '{author_name}'s homepage (author of '{paper_title}'), "
            f"select the most likely personal/professional profile. Respond with just the URL or 'None'.\n\n"
            + "\n".join(f"- {link}" for link in potential_links)
        )

        try:
            response = client.chat.completions.create(
                model=os.environ.get("OPENROUTER_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "Select personal/professional Twitter profiles for academic authors. Respond with just the URL or 'None'."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=128,
            )
            text = response.choices[0].message.content.strip()
            
            if text.startswith("http"):
                return text
            elif text.lower() == 'none':
                return ""
            else:
                return potential_links[0] if potential_links else ""
        except Exception as e:
            print(f"  ⚠️  LLM selection failed: {e}")
            return potential_links[0] if potential_links else ""

    def extract_twitter_links(self, html_content: str) -> List[str]:
        """Extract Twitter/X links from HTML content."""
        twitter_pattern = r'https?:\/\/(?:www\.)?(twitter|x)\.com\/(?!home|explore|search|intent|share|i\/events|settings|notifications|messages|compose|tos|privacy|jobs|about|download|account|help|signup|login|i\/flow|lists)([a-zA-Z0-9_]{1,15})(?:\?.*|\/.*)?'
        
        potential_links = []
        matches = re.finditer(twitter_pattern, html_content, re.IGNORECASE)
        
        for match in matches:
            url = match.group(0).rstrip('/').replace('twitter.com/', 'x.com/')
            if url not in potential_links:
                potential_links.append(url)
        
        return potential_links

    async def find_twitter_handle_for_author(self, context, author: Dict[str, Any], paper_title: str) -> None:
        """Find Twitter handle for a single author."""
        author_name = author.get("name") or author.get("openreview_id", "Unknown Author")
        homepage_url = author.get("links", {}).get("homepage")

        author["twitter_handle_url"] = None
        author["twitter_status"] = "No homepage"

        if not homepage_url or homepage_url in self.processed_urls:
            if homepage_url in self.processed_urls:
                author["twitter_status"] = "Already processed"
            else:
                self.stats['no_homepage'] += 1
            return

        self.processed_urls.add(homepage_url)
        page = None

        try:
            print(f"  🔍 Checking: {author_name}")
            
            page = await context.new_page()
            page.set_default_navigation_timeout(self.timeout)
            page.set_default_timeout(10000)
            
            await page.goto(homepage_url, wait_until='domcontentloaded')
            await page.wait_for_timeout(2000)
            
            html_content = await page.content()
            potential_links = self.extract_twitter_links(html_content)

            if not potential_links:
                author["twitter_status"] = "No Twitter handle found"
                print(f"    ❌ No handle found")
            elif len(potential_links) == 1:
                author["twitter_handle_url"] = potential_links[0]
                author["twitter_status"] = "Handle found"
                self.stats['handles_found'] += 1
                print(f"    ✅ Found: {potential_links[0]}")
            else:
                selected = self.get_most_relevant_twitter_link_via_llm(author_name, paper_title, potential_links)
                author["twitter_handle_url"] = selected if selected else None
                author["twitter_status"] = "Handle selected via LLM" if selected else "No relevant handle found"
                if selected:
                    self.stats['handles_found'] += 1
                    print(f"    🤖 Selected: {selected}")
                else:
                    print(f"    ❌ No relevant handle found")
                self.stats['multiple_handles'] += 1

        except Exception as e:
            author["twitter_status"] = f"Error: {type(e).__name__}"
            self.stats['errors'] += 1
            print(f"    ❌ Error: {e}")
        finally:
            if page and not page.is_closed():
                await page.close()

    async def process_papers(self, papers_data: List[Dict[str, Any]]) -> None:
        """Process all papers to find Twitter handles for authors."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True
            )
            
            context.set_default_navigation_timeout(self.timeout)
            context.set_default_timeout(15000)

            print(f"🐦 Starting Twitter handle search for {len(papers_data)} papers...")
            
            for i, paper in enumerate(papers_data, 1):
                paper_title = paper.get("paper_title") or paper.get("title", "Unknown Title")
                authors = paper.get("authors", [])
                
                print(f"\n📄 Paper {i}/{len(papers_data)}: {paper_title[:50]}...")
                
                if not authors:
                    continue
                
                self.stats['total_authors'] += len(authors)
                
                for j in range(0, len(authors), self.max_concurrent):
                    batch = authors[j:j + self.max_concurrent]
                    tasks = [
                        self.find_twitter_handle_for_author(context, author, paper_title)
                        for author in batch
                    ]
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
                    if j + self.max_concurrent < len(authors):
                        await asyncio.sleep(1)

            await browser.close()

    def print_statistics(self):
        """Print summary statistics."""
        print(f"\n🐦 Twitter Search Summary: {self.stats['handles_found']}/{self.stats['total_authors']} handles found")

def clean_filename(filename: str) -> str:
    """Clean filename for safe file system usage."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def calculate_author_display(authors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate which authors to display based on the new requirements:
    - Always use 3 columns
    - If <= 6 authors: show all
    - If > 6 authors: show first 5 + "N more"
    """
    total_authors = len(authors)
    
    if total_authors <= 6:
        authors_to_display = authors
        remaining_authors = 0
    else:
        authors_to_display = authors[:5]
        remaining_authors = total_authors - 5
    
    return {
        'authors_to_display': authors_to_display,
        'remaining_authors': remaining_authors,
        'total_authors': total_authors
    }

def get_logo_base64() -> str:
    """Get logo as base64 data URL."""
    current_dir = Path(__file__).parent
    logo_path = current_dir / "lossfunk_logo.png"
    
    try:
        with open(logo_path, 'rb') as f:
            logo_data = f.read()
        logo_base64 = base64.b64encode(logo_data).decode('utf-8')
        return f"data:image/png;base64,{logo_base64}"
    except FileNotFoundError:
        print(f"Warning: Logo file not found at {logo_path}")
        return ""

def calculate_title_font_size(title: str) -> int:
    """Calculate appropriate font size based on title length."""
    title_length = len(title)
    
    if title_length > 80:
        return 32
    elif title_length > 60:
        return 36
    elif title_length > 40:
        return 40
    else:
        return 44

def generate_html(paper_data: Dict[str, Any], template_path: str = None, brand_text: str = "India@ML") -> str:
    """Generate HTML content using Jinja2 template from external file."""
    current_dir = Path(__file__).parent
    
    # Use provided template path or default
    if template_path:
        template_dir = Path(template_path).parent
        template_name = Path(template_path).name
    else:
        template_dir = current_dir / "templates"
        template_name = "card_template.html"
    
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    
    # Calculate author display
    author_display = calculate_author_display(paper_data['authors'])
    
    # Get logo
    logo_base64 = get_logo_base64()
    
    # Calculate title font size
    title_font_size = calculate_title_font_size(paper_data['title'])
    
    # Render template
    html_content = template.render(
        paper=paper_data,
        authors_to_display=author_display['authors_to_display'],
        remaining_authors=author_display['remaining_authors'],
        logo_base64=logo_base64,
        title_font_size=title_font_size,
        brand_text=brand_text
    )
    
    return html_content

async def convert_html_to_image_playwright(html_content: str, output_path: str, format: str = 'png'):
    """Convert HTML to image using Playwright."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Set viewport to exact card dimensions
        await page.set_viewport_size({"width": 800, "height": 500})
        
        # Load HTML content
        await page.set_content(html_content)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)  # Allow time for fonts and rendering
        
        # Screenshot options
        screenshot_options = {
            "path": output_path,
            "full_page": False,
            "clip": {"x": 0, "y": 0, "width": 800, "height": 500}
        }
        
        if format.lower() in ['jpg', 'jpeg']:
            screenshot_options["type"] = "jpeg"
            screenshot_options["quality"] = 95
        elif format.lower() == 'webp':
            screenshot_options["type"] = "webp"
            screenshot_options["quality"] = 95
        else:
            screenshot_options["type"] = "png"
        
        await page.screenshot(**screenshot_options)
        await browser.close()

def create_merged_pdf(image_paths: List[str], output_path: str):
    """Create a merged PDF from all card images."""
    if not image_paths:
        return
    
    c = canvas.Canvas(output_path, pagesize=letter)
    page_width, page_height = letter
    
    for image_path in image_paths:
        try:
            # Open image and get dimensions
            img = Image.open(image_path)
            img_width, img_height = img.size
            
            # Calculate scaling to fit page while maintaining aspect ratio
            scale = min(page_width / img_width, page_height / img_height) * 0.9
            scaled_width = img_width * scale
            scaled_height = img_height * scale
            
            # Center image on page
            x = (page_width - scaled_width) / 2
            y = (page_height - scaled_height) / 2
            
            # Add image to PDF
            c.drawImage(ImageReader(img), x, y, scaled_width, scaled_height)
            c.showPage()
            
        except Exception as e:
            print(f"Error adding {image_path} to PDF: {e}")
    
    c.save()
    print(f"📖 Created merged PDF: {output_path}")

async def main():
    parser = argparse.ArgumentParser(description='Generate research paper cards with optional Twitter handle finding')
    parser.add_argument('input_json', help='Input JSON file with paper data')
    parser.add_argument('--find-twitter', action='store_true',
                        help='Find Twitter handles before generating cards')
    parser.add_argument('--find-twitter-only', action='store_true',
                        help='Only find Twitter handles, don\'t generate cards')
    parser.add_argument('--format', choices=['png', 'jpg', 'jpeg', 'webp'], default='png',
                        help='Output image format (default: png)')
    parser.add_argument('--output', default='output/',
                        help='Output directory (default: output/)')
    parser.add_argument('--pdf', action='store_true',
                        help='Create merged PDF with all cards')
    parser.add_argument('--max-concurrent', type=int, default=3,
                        help='Maximum concurrent Twitter searches (default: 3)')
    
    # Template and branding customization
    parser.add_argument('--template', type=str,
                        help='Path to custom HTML template file (default: templates/card_template.html)')
    parser.add_argument('--brand-text', type=str, default='India@ML',
                        help='Brand text to display on cards (default: India@ML)')
    parser.add_argument('--conference', type=str,
                        help='Override conference name for all papers')
    parser.add_argument('--presentation-type', type=str,
                        help='Override presentation type for all papers')
    
    args = parser.parse_args()
    
    # Load input data
    input_path = Path(args.input_json)
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, dict) and 'papers' in data:
        papers_data = data['papers']
        original_structure = data
    elif isinstance(data, list):
        papers_data = data
        original_structure = None
    elif isinstance(data, dict):
        papers_data = [data]
        original_structure = None
    else:
        raise ValueError("Invalid JSON structure")
    
    # Find Twitter handles if requested
    if args.find_twitter or args.find_twitter_only:
        if not client:
            print("⚠️  Warning: No OpenAI/OpenRouter API key found. Twitter handle selection will be basic.")
        
        finder = TwitterHandleFinder(max_concurrent=args.max_concurrent)
        await finder.process_papers(papers_data)
        finder.print_statistics()
        
        # Save updated data with Twitter handles
        if original_structure:
            original_structure['papers'] = papers_data
            output_data = original_structure
        else:
            output_data = papers_data
        
        twitter_output_path = input_path.with_stem(f"{input_path.stem}_with_twitter")
        with open(twitter_output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Data with Twitter handles saved to {twitter_output_path}")
    
    # Exit if only finding Twitter handles
    if args.find_twitter_only:
        return
    
    # Generate cards
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    image_paths = []
    print(f"\n🎨 Generating cards for {len(papers_data)} papers...")
    
    for i, paper in enumerate(papers_data):
        title = paper.get('title', paper.get('paper_title', 'Untitled'))
        print(f"📄 Processing {i+1}/{len(papers_data)}: {title[:50]}...")
        
        paper_data = {
            'title': title,
            'authors': paper.get('authors', []),
            'conference': args.conference or paper.get('conference', 'ICML 2025'),
            'presentation_type': args.presentation_type or paper.get('presentation_type', 'Research Paper')
        }
        
        # Generate HTML content
        html_content = generate_html(
            paper_data, 
            template_path=args.template,
            brand_text=args.brand_text
        )
        
        # Create safe filename
        safe_title = clean_filename(title[:50])
        base_filename = f"{i+1:03d}_{safe_title}"
        
        # Save HTML for debugging (optional)
        html_path = output_dir / f"{base_filename}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Convert to image
        image_path = output_dir / f"{base_filename}.{args.format}"
        await convert_html_to_image_playwright(html_content, str(image_path), args.format)
        image_paths.append(str(image_path))
        
        print(f"  ✅ Generated: {image_path}")
    
    # Create merged PDF if requested
    if args.pdf:
        pdf_path = output_dir / "merged_cards.pdf"
        create_merged_pdf(image_paths, str(pdf_path))
    
    print(f"\n🎉 Completed! Generated {len(papers_data)} cards in {output_dir}")
    
    # Show author display statistics
    for paper in papers_data:
        authors = paper.get('authors', [])
        if authors:
            display_info = calculate_author_display(authors)
            total = display_info['total_authors']
            displayed = len(display_info['authors_to_display'])
            remaining = display_info['remaining_authors']
            
            title = paper.get('title', paper.get('paper_title', 'Untitled'))[:30]
            if remaining > 0:
                print(f"  📊 {title}...: {displayed}/{total} authors displayed (+{remaining} more)")
            else:
                print(f"  📊 {title}...: {displayed}/{total} authors displayed (all)")

if __name__ == "__main__":
    asyncio.run(main())
