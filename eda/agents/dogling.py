#!/usr/bin/env python3
"""
convert_pdf_smoldocling.py

A simple script to convert a PDF to Markdown and HTML using Docling's SmolDocling VLM pipeline.
Requires:
    pip install docling
"""
import sys
from docling.document_converter import DocumentConverter

def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_pdf_smoldocling.py <input.pdf> [output_prefix]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else None

    # Initialize the converter with the SmolDocling VLM
    converter = DocumentConverter(pipeline="vlm", vlm_model="smoldocling")

    # Convert the document
    result = converter.convert(input_pdf)
    doc = result.document

    # Export to Markdown and HTML
    markdown = doc.export_to_markdown()
    try:
        html = doc.export_to_html()
    except AttributeError:
        # Fallback: wrap markdown in basic HTML
        html = f"<html><body>\n{markdown}\n</body></html>"

    # Write outputs
    if output_prefix:
        md_path = f"{output_prefix}.md"
        html_path = f"{output_prefix}.html"
        with open(md_path, "w", encoding="utf-8") as md_file:
            md_file.write(markdown)
        with open(html_path, "w", encoding="utf-8") as html_file:
            html_file.write(html)
        print(f"Saved Markdown to {md_path} and HTML to {html_path}")
    else:
        # Print to stdout
        print("--- Markdown Output ---")
        print(markdown)
        print("--- HTML Output ---")
        print(html)

if __name__ == "__main__":
    main()
