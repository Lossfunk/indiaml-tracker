#!/usr/bin/env python3
import argparse
import base64
import csv
import pathlib
from pathlib import Path
import requests
import tempfile
import json
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY", "sk-or-v1-..."),
    base_url="https://openrouter.ai/api/v1",
)


PROMPT = """Here's my theory of the formula behind successful startups. Every successful startup targets an existing demonstrated behavior of a customer or a user, and provides a solution that radically improves in efficiency over the status quo. (E.g. before Uber people used to call for taxis, but Uber made it 10x easier to hail a cab with a click of a button, same with Amazon. Before Amazon book lovers would need to search in multiple book stores to find their books but amazon made it easy to find any book online) Now, I will give you a research paper and you need to think whether the research from the paper can lead to a startup idea or commercial application.  Think step by step and cite real world evidence when you think (ground your assumptions in reality). Rate attractiveness of the startup idea from 1 to 5 based on my theory above, then criticise yourself and revise the rating. If no startup idea is possible, rate it 0. Attractiveness is defined as how much better the startup solution can be over current alternatives. If it is radically (10x better), rate it close to 5. If it is just an incremental improvement, rate it close to 1. Please note that 10x better solutions are very rare and papers rarely lead to breakthrough startups, so be critical and rate high only if you're absolutely convinced. Give a detailed explanation, and also clearly give a super-concrete example of the top use case so that a human rater can immediately understand your explanation for rating."""


def encode_pdf_to_base64(pdf_path: str) -> str:
    """Encode a PDF file as a data URL with base64 content."""
    with open(pdf_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")
    return f"data:application/pdf;base64,{content}"


def download_pdf(url: str) -> str:
    print(f"Downloading PDF from: {url}")
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    with tmp as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)

    return tmp.name


def summarize_paper_openrouter(
    pdf_path: str, prompt: str, model: str, engine: str = "pdf-text"
) -> str:
    """
    Encode a PDF, then send it with the prompt to OpenRouter via the chat API using requests.
    """
    # encode the PDF
    data_url = encode_pdf_to_base64(pdf_path)
    filename = os.path.basename(pdf_path)
    
    # Set up the request
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY', 'sk-or-v1-...')}",
        "Content-Type": "application/json"
    }
    
    # build messages array per OpenRouter PDF support
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "file",
                    "file": {"filename": filename, "file_data": data_url},
                },
            ],
        }
    ]

    # plugin config for PDF processing
    plugins = [{"id": "file-parser", "pdf": {"engine": engine}}]
    
    # Create payload
    payload = {
        "model": model,
        "messages": messages,
        "plugins": plugins,
        "max_tokens": 1000
    }
    
    # Make the request
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    # Check for errors
    if "error" in response_data:
        raise Exception(f"API Error: {response_data['error']}")
    
    # Extract the content
    if "choices" in response_data and len(response_data["choices"]) > 0:
        content = response_data["choices"][0]["message"]["content"]
    else:
        raise Exception("No content in response")
    
    # cleanup
    try:
        os.unlink(pdf_path)
    except:
        pass

    return content.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate startup potential from OpenReview papers using OpenRouter API."
    )
    parser.add_argument(
        "csv_in",
        type=pathlib.Path,
        help="Input CSV with columns: title,status,url_path[,summary]",
    )
    parser.add_argument(
        "--csv_out",
        type=pathlib.Path,
        default=None,
        help="Output CSV path (defaults to overwriting input)",
    )
    parser.add_argument(
        "--model", default="openai/gpt-4o-mini", help="Model to use (e.g., openai/gpt-4o-mini, google/gemini-pro)"
    )
    args = parser.parse_args()

    if not args.csv_in.is_file():
        raise SystemExit(f"Error: '{args.csv_in}' not found")

    csv_out = args.csv_out or args.csv_in

    base_url = "https://openreview.net"

    # Read all rows
    with args.csv_in.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        if "summary" not in fieldnames:
            fieldnames.append("summary")
        rows = list(reader)

    # Process rows
    for row in rows:
        title = row.get("title", "<no title>")
        already = row.get("summary", "")
        # print("already", row)
        if already and already.strip():
            print(f"Skipping '{title}' (summary exists)")
            continue

        url_field = " url"  # Note the space before "url"
        if url_field not in row:
            print(f"Skipping '{title}' (no URL found)")
            continue
            
        pdf_url = base_url + row[url_field]
        print(f"Summarizing '{title}'...")
        try:
            # Download the PDF first
            pdf_path = download_pdf(pdf_url)
            
            # Then summarize it
            summary = summarize_paper_openrouter(
                pdf_path, PROMPT, args.model
            )
            row["summary"] = summary
            print(f"Successfully summarized '{title}'")
        except Exception as e:
            print(f"  → Error: {e}")
        finally:
            # Clean up temp file if it exists
            if 'pdf_path' in locals():
                try:
                    if os.path.exists(pdf_path):
                        os.unlink(pdf_path)
                except Exception as e:
                    print(f"Failed to delete temp file: {e}")

    # Write out CSV
    with csv_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done. Updated CSV saved to '{csv_out}'")


if __name__ == "__main__":
    main()