#!/usr/bin/env python3
"""
Integrated Research Paper Card Generator with Twitter Handle Finder

Generates social media cards for research papers and optionally finds Twitter handles for authors.
Outputs SVG, converts to various image formats using Playwright, and creates a merged PDF.

Usage:
    # Generate cards only
    python integrated_generator.py input.json --format png --output cards/
    
    # Find Twitter handles first, then generate cards
    python integrated_generator.py input.json --find-twitter --format png --output cards/
    
    # Update existing data with Twitter handles only
    python integrated_generator.py input.json --find-twitter-only --output updated.json
    
Requirements:
    pip install playwright pillow reportlab openai python-dotenv
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

load_dotenv()

# Initialize OpenAI client for Twitter handle finding
try:
    client = OpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", os.environ.get("OPENAI_API_KEY")),
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )
except Exception:
    client = None

# SVG Template (same as before)
SVG_TEMPLATE = '''<svg viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Single color gradient for background -->
    <linearGradient id="backgroundGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#f8fafc;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#f1f5f9;stop-opacity:1" />
    </linearGradient>
    
    <!-- Dot pattern with configurable parameters -->
    <pattern id="dotGrid" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
      <circle cx="10" cy="10" r="1.5" fill="#64748b" opacity="0.12"/>
    </pattern>
    
    <!-- Subtle shadow filter -->
    <filter id="cardShadow" x="-50%" y="-50%" width="200%" height="200%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#000000" flood-opacity="0.08"/>
    </filter>
  </defs>
  
  <!-- Main card background -->
  <rect width="800" height="500" fill="url(#backgroundGradient)" filter="url(#cardShadow)" rx="16"/>
  
  <!-- Dot grid background -->
  <rect width="800" height="500" fill="url(#dotGrid)" rx="16"/>
  
  <!-- Conference info -->
  <text x="60" y="80" fill="#64748b" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="600">{{CONFERENCE}}</text>
  <text x="{{CONFERENCE_X_OFFSET}}" y="80" fill="#64748b" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="500">• {{PRESENTATION_TYPE}}</text>
  
  <!-- Lossfunk logo and India@ML branding container -->
  <g id="branding-container">
    <!-- Lossfunk logo -->
    <image x="550" y="55" height="30" href="{{LOSSFUNK_LOGO_PATH}}" preserveAspectRatio="xMidYMid meet"/>
    
    <!-- India@ML text -->
    <text x="620" y="80" fill="#64748b" font-family="system-ui, -apple-system, sans-serif" font-size="16" font-weight="600">India@ML</text>
  </g>
  
  {{TITLE_LINES}}
  
  <!-- Authors section -->
  <text x="60" y="{{AUTHORS_LABEL_Y}}" fill="#64748b" font-family="system-ui, -apple-system, sans-serif" font-size="16" font-weight="600">AUTHORS</text>
  
  {{AUTHORS}}
</svg>'''

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

# Card generation functions (same as before, but simplified for space)
def clean_filename(filename: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def wrap_title(title: str, max_chars_per_line: int = 30) -> List[str]:
    words = title.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + len(current_line) <= max_chars_per_line:
            current_line.append(word)
            current_length += len(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                lines.append(word)
                current_line = []
                current_length = 0
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def calculate_dynamic_layout(title: str, authors: List[Dict[str, str]]) -> Dict[str, Any]:
    lines = wrap_title(title)
    title_base_y = 140
    title_line_height = 55
    title_end_y = title_base_y + (len(lines) * title_line_height)
    buffer_space = 40
    authors_label_y = title_end_y + buffer_space
    authors_start_y = authors_label_y + 36
    
    max_authors_display = 10
    authors_to_show = min(len(authors), max_authors_display)
    remaining_authors = max(0, len(authors) - max_authors_display)
    
    if authors_to_show <= 3:
        cols = authors_to_show
    elif authors_to_show <= 6:
        cols = 3
    else:
        cols = 4
    
    return {
        'title_lines': lines,
        'title_base_y': title_base_y,
        'title_line_height': title_line_height,
        'authors_label_y': authors_label_y,
        'authors_start_y': authors_start_y,
        'authors_to_show': authors_to_show,
        'remaining_authors': remaining_authors,
        'grid_cols': cols,
    }

def get_logo_base64() -> str:
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

def generate_svg(paper_data: Dict[str, Any]) -> str:
    layout = calculate_dynamic_layout(paper_data['title'], paper_data['authors'])
    
    # Generate title
    title_svg = ""
    for i, line in enumerate(layout['title_lines']):
        y_pos = layout['title_base_y'] + (i * layout['title_line_height'])
        title_svg += f'  <text x="60" y="{y_pos}" fill="#1e293b" font-family="Georgia, \'Times New Roman\', serif" font-size="42" font-weight="700">{line}</text>\n'
    
    # Generate authors (simplified)
    authors_svg = ""
    cols = layout['grid_cols']
    base_x, base_y = 60, layout['authors_start_y']
    col_width, row_height = 190, 40
    
    authors_to_display = paper_data['authors'][:layout['authors_to_show']]
    
    for i, author in enumerate(authors_to_display):
        row, col = i // cols, i % cols
        x_pos = base_x + (col * col_width)
        y_pos = base_y + (row * row_height)
        
        # Simple flag representation
        flag = author.get("flag", "🌐")
        authors_svg += f'  <text x="{x_pos}" y="{y_pos}" fill="#374151" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="500">{flag} {author["name"]}</text>\n'
    
    if layout['remaining_authors'] > 0:
        authors_svg += f'  <text x="{base_x}" y="{base_y + ((layout["authors_to_show"] // cols + 1) * row_height)}" fill="#64748b" font-family="system-ui, -apple-system, sans-serif" font-size="16" font-weight="500" font-style="italic">+{layout["remaining_authors"]} more</text>\n'
    
    # Replace template
    svg_content = SVG_TEMPLATE.replace('{{TITLE_LINES}}', title_svg)
    svg_content = svg_content.replace('{{AUTHORS}}', authors_svg)
    svg_content = svg_content.replace('{{AUTHORS_LABEL_Y}}', str(layout['authors_label_y']))
    svg_content = svg_content.replace('{{CONFERENCE}}', paper_data['conference'])
    svg_content = svg_content.replace('{{PRESENTATION_TYPE}}', paper_data['presentation_type'])
    svg_content = svg_content.replace('{{CONFERENCE_X_OFFSET}}', str(80 + len(paper_data['conference']) * 10))
    svg_content = svg_content.replace('{{LOSSFUNK_LOGO_PATH}}', get_logo_base64())
    
    return svg_content

async def convert_svg_to_image_playwright(svg_content: str, output_path: str, format: str = 'png'):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background: transparent; width: 800px; height: 500px; }}
            svg {{ display: block; width: 800px; height: 500px; }}
        </style>
    </head>
    <body>{svg_content}</body>
    </html>
    """
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.set_viewport_size({"width": 800, "height": 500})
        await page.set_content(html_content)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(500)
        
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
            'conference': paper.get('conference', 'ICML 2025'),
            'presentation_type': paper.get('presentation_type', 'Research Paper')
        }
        
        svg_content = generate_svg(paper_data)
        
        safe_title = clean_filename(title[:50])
        base_filename = f"{i+1:03d}_{safe_title}"
        
        # Save SVG
        svg_path = output_dir / f"{base_filename}.svg"
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        # Convert to image
        image_path = output_dir / f"{base_filename}.{args.format}"
        await convert_svg_to_image_playwright(svg_content, str(image_path), args.format)
        image_paths.append(str(image_path))
        
        print(f"  ✅ Generated: {image_path}")
    
    print(f"\n🎉 Completed! Generated {len(papers_data)} cards in {output_dir}")

if __name__ == "__main__":
    asyncio.run(main())