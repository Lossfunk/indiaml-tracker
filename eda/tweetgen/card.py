#!/usr/bin/env python3
"""
Research Paper Card Generator

Generates social media cards for research papers from JSON data.
Outputs SVG, converts to various image formats, and creates a merged PDF.

Usage:
    python paper_card_generator.py input.json --format png --output cards/
    
Requirements:
    pip install cairosvg pillow reportlab
"""

import json
import argparse
import os
from pathlib import Path
import re
from typing import List, Dict, Any
import cairosvg
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import io

# SVG Template
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
  
  <!-- India@ML branding -->
  <text x="580" y="80" fill="#64748b" font-family="system-ui, -apple-system, sans-serif" font-size="16" font-weight="600">India@ML</text>
  
  <!-- Lossfunk logo placeholder -->
  <rect x="680" y="60" width="60" height="40" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1" rx="8"/>
  <text x="710" y="75" text-anchor="middle" fill="#64748b" font-family="system-ui, -apple-system, sans-serif" font-size="10" font-weight="500">LOSSFUNK</text>
  <text x="710" y="88" text-anchor="middle" fill="#64748b" font-family="system-ui, -apple-system, sans-serif" font-size="8">LOGO</text>
  
  {{TITLE_LINES}}
  
  <!-- Authors section -->
  <text x="60" y="260" fill="#64748b" font-family="system-ui, -apple-system, sans-serif" font-size="16" font-weight="600">AUTHORS</text>
  
  {{AUTHORS}}
</svg>'''

def clean_filename(filename: str) -> str:
    """Clean filename for filesystem compatibility."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def wrap_title(title: str, max_chars_per_line: int = 35) -> List[str]:
    """Wrap title into multiple lines."""
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
                # Word is too long, add it anyway
                lines.append(word)
                current_line = []
                current_length = 0
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def generate_title_svg(title: str) -> str:
    """Generate SVG text elements for title."""
    lines = wrap_title(title)
    title_svg = ""
    base_y = 140
    
    for i, line in enumerate(lines):
        y_pos = base_y + (i * 55)
        title_svg += f'  <text x="60" y="{y_pos}" fill="#1e293b" font-family="Georgia, \'Times New Roman\', serif" font-size="42" font-weight="700">\n'
        title_svg += f'    {line}\n'
        title_svg += f'  </text>\n'
    
    return title_svg

def emoji_flag_to_country_code(emoji_flag: str) -> str:
    """Convert emoji flag to country code."""
    flag_to_code = {
        "🇮🇳": "IN",
        "🇺🇸": "US", 
        "🇬🇧": "GB",
        "🇨🇦": "CA",
        "🇩🇪": "DE",
        "🇯🇵": "JP",
        "🇫🇷": "FR",
        "🇦🇺": "AU",
        "🇨🇳": "CN",
        "🇰🇷": "KR",
        "🇧🇷": "BR",
        "🇮🇹": "IT",
        "🇪🇸": "ES",
        "🇳🇱": "NL",
        "🇸🇪": "SE",
        "🇨🇭": "CH",
        "🇦🇹": "AT",
        "🇧🇪": "BE",
        "🇩🇰": "DK",
        "🇫🇮": "FI",
        "🇳🇴": "NO",
        "🇵🇱": "PL",
        "🇷🇺": "RU",
        "🇮🇱": "IL",
        "🇸🇬": "SG",
        "🇭🇰": "HK",
        "🇹🇼": "TW",
        "🇹🇭": "TH",
        "🇲🇽": "MX",
        "🇦🇷": "AR",
        "🇿🇦": "ZA",
        "🇪🇬": "EG",
        "🇳🇬": "NG",
        "🇰🇪": "KE",
        "🇬🇭": "GH",
        "🇲🇦": "MA",
        "🇹🇳": "TN",
        "🇪🇹": "ET",
        "🇺🇬": "UG",
        "🇹🇿": "TZ",
        "🇷🇼": "RW",
        "🇸🇳": "SN",
        "🇨🇮": "CI",
        "🇧🇫": "BF",
        "🇲🇱": "ML",
        "🇳🇪": "NE",
        "🇹🇩": "TD",
        "🇨🇫": "CF",
        "🇨🇲": "CM",
        "🇬🇦": "GA",
        "🇨🇬": "CG",
        "🇨🇩": "CD",
        "🇦🇴": "AO",
        "🇿🇲": "ZM",
        "🇿🇼": "ZW",
        "🇧🇼": "BW",
        "🇳🇦": "NA",
        "🇸🇿": "SZ",
        "🇱🇸": "LS",
        "🇲🇼": "MW",
        "🇲🇿": "MZ",
        "🇲🇬": "MG",
        "🇲🇺": "MU",
        "🇸🇨": "SC",
        "🇰🇲": "KM",
        "🇩🇯": "DJ",
        "🇸🇴": "SO",
        "🇪🇷": "ER",
        "🇸🇩": "SD",
        "🇸🇸": "SS",
        "🇱🇾": "LY",
        "🇩🇿": "DZ",
        "🇲🇷": "MR",
        "🇲🇱": "ML",
        "🇸🇳": "SN",
        "🇬🇲": "GM",
        "🇬🇼": "GW",
        "🇨🇻": "CV",
        "🇸🇱": "SL",
        "🇱🇷": "LR",
        "🇬🇳": "GN"
    }
    return flag_to_code.get(emoji_flag, emoji_flag)

def get_flag_color(country_code: str) -> str:
    """Get a representative color for country flags."""
    colors = {
        "IN": "#FF9933",  # India - saffron
        "US": "#B22234",  # USA - red
        "GB": "#012169",  # UK - blue
        "CA": "#FF0000",  # Canada - red
        "DE": "#000000",  # Germany - black
        "JP": "#BC002D",  # Japan - red
        "FR": "#0055A4",  # France - blue
        "AU": "#00008B",  # Australia - blue
        "CN": "#DE2910",  # China - red
        "KR": "#003478",  # South Korea - blue
        "BR": "#009739",  # Brazil - green
        "IT": "#009246",  # Italy - green
        "ES": "#AA151B",  # Spain - red
        "NL": "#21468B",  # Netherlands - blue
        "SE": "#006AA7",  # Sweden - blue
        "CH": "#FF0000",  # Switzerland - red
        "AT": "#ED2939",  # Austria - red
        "BE": "#000000",  # Belgium - black
        "DK": "#C60C30",  # Denmark - red
        "FI": "#003580",  # Finland - blue
        "NO": "#EF2B2D",  # Norway - red
        "PL": "#DC143C",  # Poland - red
        "RU": "#0039A6",  # Russia - blue
        "IL": "#0038B8",  # Israel - blue
        "SG": "#ED2939",  # Singapore - red
        "HK": "#DE2910",  # Hong Kong - red
        "TW": "#FE0000",  # Taiwan - red
        "TH": "#A51931",  # Thailand - red
        "MX": "#006847",  # Mexico - green
        "AR": "#74ACDF",  # Argentina - light blue
        "ZA": "#007A4D",  # South Africa - green
    }
    return colors.get(country_code, "#64748b")  # Default gray

def generate_authors_svg(authors: List[Dict[str, str]]) -> str:
    """Generate SVG text elements for authors with flag representation."""
    authors_svg = ""
    cols = 3
    base_x = 60
    base_y = 296
    col_width = 190
    row_height = 40
    
    for i, author in enumerate(authors):
        row = i // cols
        col = i % cols
        
        x_pos = base_x + (col * col_width)
        y_pos = base_y + (row * row_height)
        
        # Convert emoji flag to country code
        country_code = emoji_flag_to_country_code(author["flag"])
        flag_color = get_flag_color(country_code)
        
        # Create a colored rectangle as flag representation
        authors_svg += f'  <rect x="{x_pos}" y="{y_pos - 12}" width="20" height="12" fill="{flag_color}" rx="2"/>\n'
        # Add country code text on the flag
        authors_svg += f'  <text x="{x_pos + 10}" y="{y_pos - 3}" text-anchor="middle" fill="white" font-family="system-ui, -apple-system, sans-serif" font-size="8" font-weight="600">{country_code}</text>\n'
        # Name
        authors_svg += f'  <text x="{x_pos + 25}" y="{y_pos + 4}" fill="#374151" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="500">{author["name"]}</text>\n'
    
    return authors_svg

def calculate_conference_offset(conference: str) -> int:
    """Calculate x-offset for presentation type based on conference name length."""
    base_offset = 180
    char_width = 10  # Approximate character width
    return base_offset + len(conference) * char_width

def generate_svg(paper_data: Dict[str, Any]) -> str:
    """Generate SVG for a single paper."""
    title_svg = generate_title_svg(paper_data['title'])
    authors_svg = generate_authors_svg(paper_data['authors'])
    conference_offset = calculate_conference_offset(paper_data['conference'])
    
    svg_content = SVG_TEMPLATE.replace('{{TITLE_LINES}}', title_svg)
    svg_content = svg_content.replace('{{AUTHORS}}', authors_svg)
    svg_content = svg_content.replace('{{CONFERENCE}}', paper_data['conference'])
    svg_content = svg_content.replace('{{PRESENTATION_TYPE}}', paper_data['presentation_type'])
    svg_content = svg_content.replace('{{CONFERENCE_X_OFFSET}}', str(conference_offset))
    
    return svg_content

def convert_svg_to_image(svg_content: str, output_path: str, format: str):
    """Convert SVG to specified image format."""
    if format.lower() == 'png':
        cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), write_to=output_path, dpi=300)
    elif format.lower() == 'jpg' or format.lower() == 'jpeg':
        # Convert to PNG first, then to JPG
        png_bytes = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), dpi=300)
        img = Image.open(io.BytesIO(png_bytes))
        # Convert RGBA to RGB for JPG
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1])
            img = rgb_img
        img.save(output_path, 'JPEG', quality=95)
    elif format.lower() == 'webp':
        # Convert to PNG first, then to WebP
        png_bytes = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), dpi=300)
        img = Image.open(io.BytesIO(png_bytes))
        img.save(output_path, 'WebP', quality=95)
    else:
        raise ValueError(f"Unsupported format: {format}")

def create_pdf(image_paths: List[str], output_path: str):
    """Create PDF with all images as pages."""
    c = canvas.Canvas(output_path, pagesize=letter)
    page_width, page_height = letter
    
    for image_path in image_paths:
        # Calculate image dimensions to fit page
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        # Calculate scaling to fit page with margins
        margin = 50
        available_width = page_width - 2 * margin
        available_height = page_height - 2 * margin
        
        scale_x = available_width / img_width
        scale_y = available_height / img_height
        scale = min(scale_x, scale_y)
        
        new_width = img_width * scale
        new_height = img_height * scale
        
        # Center the image
        x = (page_width - new_width) / 2
        y = (page_height - new_height) / 2
        
        c.drawImage(ImageReader(image_path), x, y, new_width, new_height)
        c.showPage()
    
    c.save()

def main():
    parser = argparse.ArgumentParser(description='Generate research paper cards from JSON data')
    parser.add_argument('input_json', help='Input JSON file with paper data')
    parser.add_argument('--format', choices=['png', 'jpg', 'jpeg', 'webp'], default='png',
                        help='Output image format (default: png)')
    parser.add_argument('--output', default='output/',
                        help='Output directory (default: output/)')
    parser.add_argument('--pdf', action='store_true',
                        help='Create merged PDF with all cards')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load JSON data
    with open(args.input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, dict) and 'papers' in data:
        # JSON has structure: {"papers": [...]}
        papers_data = data['papers']
    elif isinstance(data, list):
        # JSON is already a list of papers
        papers_data = data
    elif isinstance(data, dict):
        # JSON is a single paper object
        papers_data = [data]
    else:
        raise ValueError("Invalid JSON structure. Expected a list of papers or an object with 'papers' key.")
    
    image_paths = []
    
    for i, paper in enumerate(papers_data):
        print(f"Processing paper {i+1}/{len(papers_data)}: {paper['title'][:50]}...")
        
        # Generate SVG
        svg_content = generate_svg(paper)
        
        # Create filename
        safe_title = clean_filename(paper['title'][:50])
        base_filename = f"{i+1:03d}_{safe_title}"
        
        # Save SVG
        svg_path = output_dir / f"{base_filename}.svg"
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        # Convert to specified format
        image_path = output_dir / f"{base_filename}.{args.format}"
        convert_svg_to_image(svg_content, str(image_path), args.format)
        image_paths.append(str(image_path))
        
        print(f"Generated: {image_path}")
    
    # Create PDF if requested
    if args.pdf:
        pdf_path = output_dir / "papers_cards.pdf"
        create_pdf(image_paths, str(pdf_path))
        print(f"Created PDF: {pdf_path}")
    
    print(f"\nCompleted! Generated {len(papers_data)} cards in {output_dir}")

# Example JSON structure
EXAMPLE_JSON = {
    "papers": [
        {
            "title": "Multi-modal brain encoding models for cognitive processing",
            "authors": [
                {"name": "S. R. OOTA", "flag": "🇮🇳"},
                {"name": "K. PAHWA", "flag": "🇺🇸"},
                {"name": "M. MARREDDY", "flag": "🇬🇧"},
                {"name": "J. WILSON", "flag": "🇨🇦"},
                {"name": "L. ZHANG", "flag": "🇩🇪"},
                {"name": "N. PATEL", "flag": "🇯🇵"},
                {"name": "A. RODRIGUEZ", "flag": "🇫🇷"},
                {"name": "K. MULLER", "flag": "🇦🇺"}
            ],
            "conference": "ICML 2025",
            "presentation_type": "Spotlight paper"
        }
    ]
}

if __name__ == "__main__":
    # Create example JSON file if it doesn't exist
    if not os.path.exists("example_papers.json"):
        with open("example_papers.json", 'w', encoding='utf-8') as f:
            json.dump(EXAMPLE_JSON, f, indent=2, ensure_ascii=False)
        print("Created example_papers.json - you can use this as a template!")
    
    main()
