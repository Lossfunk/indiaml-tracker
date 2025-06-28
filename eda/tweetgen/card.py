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
import base64

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
  
  <!-- Lossfunk logo and India@ML branding container (constrained to max width) -->
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

def clean_filename(filename: str) -> str:
    """Clean filename for filesystem compatibility."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def wrap_title(title: str, max_chars_per_line: int = 30) -> List[str]:
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

def calculate_dynamic_layout(title: str, authors: List[Dict[str, str]]) -> Dict[str, Any]:
    """Calculate dynamic layout positions to prevent overlapping."""
    lines = wrap_title(title)
    
    # Title positioning
    title_base_y = 140
    title_line_height = 55
    title_end_y = title_base_y + (len(lines) * title_line_height)
    
    # Authors section positioning with buffer
    buffer_space = 40
    authors_label_y = title_end_y + buffer_space
    authors_start_y = authors_label_y + 36  # Space for "AUTHORS" label
    
    # Author grid calculation
    max_authors_display = 10
    authors_to_show = min(len(authors), max_authors_display)
    remaining_authors = max(0, len(authors) - max_authors_display)
    
    # Grid layout - adjust columns based on number of authors
    if authors_to_show <= 3:
        cols = authors_to_show
    elif authors_to_show <= 6:
        cols = 3
    else:
        cols = 4
    
    rows = (authors_to_show + cols - 1) // cols  # Ceiling division
    
    return {
        'title_lines': lines,
        'title_base_y': title_base_y,
        'title_line_height': title_line_height,
        'authors_label_y': authors_label_y,
        'authors_start_y': authors_start_y,
        'authors_to_show': authors_to_show,
        'remaining_authors': remaining_authors,
        'grid_cols': cols,
        'grid_rows': rows
    }

def generate_title_svg(title: str, layout: Dict[str, Any]) -> str:
    """Generate SVG text elements for title using dynamic layout."""
    title_svg = ""
    
    for i, line in enumerate(layout['title_lines']):
        y_pos = layout['title_base_y'] + (i * layout['title_line_height'])
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

def generate_authors_svg(authors: List[Dict[str, str]], layout: Dict[str, Any]) -> str:
    """Generate SVG text elements for authors with flag representation using dynamic layout."""
    authors_svg = ""
    
    # Use layout parameters
    cols = layout['grid_cols']
    base_x = 60
    base_y = layout['authors_start_y']
    col_width = 190
    row_height = 40
    
    # Show only the authors that fit (max 10)
    authors_to_display = authors[:layout['authors_to_show']]
    
    for i, author in enumerate(authors_to_display):
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
    
    # Add "+X more" if there are remaining authors
    if layout['remaining_authors'] > 0:
        # Calculate position for "+X more" text
        total_displayed = layout['authors_to_show']
        last_row = (total_displayed - 1) // cols
        last_col = (total_displayed - 1) % cols
        
        # Position "+X more" in the next available slot
        if last_col + 1 < cols:
            # Same row, next column
            more_row = last_row
            more_col = last_col + 1
        else:
            # Next row, first column
            more_row = last_row + 1
            more_col = 0
        
        more_x_pos = base_x + (more_col * col_width)
        more_y_pos = base_y + (more_row * row_height)
        
        # Add "+X more" text
        authors_svg += f'  <text x="{more_x_pos}" y="{more_y_pos + 4}" fill="#64748b" font-family="system-ui, -apple-system, sans-serif" font-size="16" font-weight="500" font-style="italic">+{layout["remaining_authors"]} more</text>\n'
    
    return authors_svg

def calculate_conference_offset(conference: str) -> int:
    """Calculate x-offset for presentation type based on conference name length."""
    base_offset = 80
    char_width = 10  # Approximate character width
    return base_offset + len(conference) * char_width

def get_logo_base64() -> str:
    """Convert lossfunk logo to base64 data URI."""
    current_dir = Path(__file__).parent
    logo_path = current_dir / "lossfunk_logo.png"
    
    try:
        with open(logo_path, 'rb') as f:
            logo_data = f.read()
        
        # Convert to base64
        logo_base64 = base64.b64encode(logo_data).decode('utf-8')
        return f"data:image/png;base64,{logo_base64}"
    except FileNotFoundError:
        print(f"Warning: Logo file not found at {logo_path}")
        return ""

def generate_svg(paper_data: Dict[str, Any]) -> str:
    """Generate SVG for a single paper using dynamic layout."""
    # Calculate dynamic layout
    layout = calculate_dynamic_layout(paper_data['title'], paper_data['authors'])
    
    # Generate components using layout
    title_svg = generate_title_svg(paper_data['title'], layout)
    authors_svg = generate_authors_svg(paper_data['authors'], layout)
    conference_offset = calculate_conference_offset(paper_data['conference'])
    
    # Get the lossfunk logo as base64 data URI
    logo_data_uri = get_logo_base64()
    
    # Replace template placeholders
    svg_content = SVG_TEMPLATE.replace('{{TITLE_LINES}}', title_svg)
    svg_content = svg_content.replace('{{AUTHORS}}', authors_svg)
    svg_content = svg_content.replace('{{AUTHORS_LABEL_Y}}', str(layout['authors_label_y']))
    svg_content = svg_content.replace('{{CONFERENCE}}', paper_data['conference'])
    svg_content = svg_content.replace('{{PRESENTATION_TYPE}}', paper_data['presentation_type'])
    svg_content = svg_content.replace('{{CONFERENCE_X_OFFSET}}', str(conference_offset))
    svg_content = svg_content.replace('{{LOSSFUNK_LOGO_PATH}}', logo_data_uri)
    
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
        # Handle both 'title' and 'paper_title' keys
        title = paper.get('title', paper.get('paper_title', 'Untitled'))
        print(f"Processing paper {i+1}/{len(papers_data)}: {title[:50]}...")
        
        # Ensure paper has the expected format for generate_svg
        paper_data = {
            'title': title,
            'authors': paper.get('authors', []),
            'conference': paper.get('conference', 'ICML 2025'),
            'presentation_type': paper.get('presentation_type', 'Research Paper')
        }
        
        # Generate SVG
        svg_content = generate_svg(paper_data)
        
        # Create filename
        safe_title = clean_filename(title[:50])
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
