#!/usr/bin/env python3
import argparse
import csv
import pathlib
import requests
import tempfile
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY", "sk-or-v1-..."),
    base_url="https://openrouter.ai/api/v1",
)


PROMPT = """Here's my theory of the formula behind successful startups. Every successful startup targets an existing demonstrated behavior of a customer or a user, and provides a solution that radically improves in efficiency over the status quo. (E.g. before Uber people used to call for taxis, but Uber made it 10x easier to hail a cab with a click of a button, same with Amazon. Before Amazon book lovers would need to search in multiple book stores to find their books but amazon made it easy to find any book online) Now, I will give you a research paper and you need to think whether the research from the paper can lead to a startup idea or commercial application.  Think step by step and cite real world evidence when you think (ground your assumptions in reality). Rate attractiveness of the startup idea from 1 to 5 based on my theory above, then criticise yourself and revise the rating. If no startup idea is possible, rate it 0. Attractiveness is defined as how much better the startup solution can be over current alternatives. If it is radically (10x better), rate it close to 5. If it is just an incremental improvement, rate it close to 1. Please note that 10x better solutions are very rare and papers rarely lead to breakthrough startups, so be critical and rate high only if you're absolutely convinced. Give a detailed explanation, and also clearly give a super-concrete example of the top use case so that a human rater can immediately understand your explanation for rating."""

def download_pdf(url: str) -> pathlib.Path:
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    with tmp as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)
    return pathlib.Path(tmp.name)



def summarize_paper_openai(pdf_path: pathlib.Path, client: OpenAI, model: str, prompt: str) -> str:
    uploaded = client.files.upload(
        file=pdf_path.open("rb"),
        config={"mime_type": "application/pdf"}
    )

    response = client.chat.completions.create(
        model="anthropic/claude-3.7-sonnet",
        messages=[
            {"role": "system", "content": "You are a helpful analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        logprobs=True,
        max_tokens=512,
    )

    return response.choices[0].message.content.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Append Gemini summaries to a CSV of OpenReview papers."
    )
    parser.add_argument(
        "csv_in",
        type=pathlib.Path,
        help="Input CSV with columns: title,status,url_path[,summary]"
    )
    parser.add_argument(
        "--csv_out",
        type=pathlib.Path,
        default=None,
        help="Output CSV path (defaults to overwriting input)"
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-pro-exp-03-25",
        help="Gemini model to use"
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
        
        print(row[" url"])
        pdf_url = base_url + row[" url"]
        print(f"Summarizing '{title}'...")
        try:
            pdf_path = download_pdf(pdf_url)
            summary = summarize_paper_openai(pdf_path, client, args.model, PROMPT)
            row["summary"] = summary
        except Exception as e:
            print(f"  → Error: {e}")
        finally:
            try:
                pdf_path.unlink()
            except:
                pass

    # Write out CSV
    with csv_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done. Updated CSV saved to '{csv_out}'")

if __name__ == "__main__":
    main()
