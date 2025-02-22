import sys
from io import BytesIO
import json
import os
import tempfile
import requests
import pymupdf4llm  # Ensure pymupdf4llm is installed and imported correctly
import openai
from dotenv import load_dotenv
load_dotenv()

# Set your OpenAI API key (or use environment variable OPENAI_API_KEY)
client = openai.OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY", "sk-or-v1-..."),
    base_url="https://openrouter.ai/api/v1",
)

print(os.environ.get("OPENROUTER_API_KEY", "sk-or-v1-..."))

# Function to download PDF
def download_pdf(pdf_url):
    """
    Download the PDF from the given URL.
    """
    print("Starting download")
    response = requests.get(pdf_url)
    response.raise_for_status()
    print("Returning BytesIO")
    return BytesIO(response.content)

# Function to convert PDF to Markdown using pymupdf4llm
def convert_pdf_to_markdown(pdf_stream, num_pages=3):
    """
    Convert the first `num_pages` of the PDF to Markdown using pymupdf4llm.
    """
    # Create a temporary file to save the PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_stream.read())
        temp_pdf_path = temp_pdf.name
    try:
        # Call the to_markdown function with the temporary file path
        markdown = pymupdf4llm.to_markdown(temp_pdf_path, pages=range(0, num_pages))
    finally:
        # Clean up the temporary file
        os.remove(temp_pdf_path)
    return markdown

def summarize_paper_goal(text: str) -> str:
    """Uses the OpenAI Chat API to summarize the paper's goal based on the extracted text."""
    response = client.chat.completions.create(
        model="google/gemini-flash-1.5-8b",  # Change this to your desired model if needed
        messages=[
            {"role": "system", "content": "You are extremely efficient and formal at writing summaries from papers. You try to write summaries intended to be read by an audience on a webpage."},
            {"role": "user", "content": f"Based on the following excerpt from a research paper, summarize the paper's goal, keep it very brief, within 2 to 3 sentences:\n\n{text}"}
        ]
    )
    return response.choices[0].message.content

def main():
    # Read input filename from CLI arguments; default to 'neurips-icml-2024.json' if none is provided.
    input_filename = sys.argv[1] if len(sys.argv) > 1 else "neurips-icml-2024.json"
    
    # Construct the output filename by adding '-papers.json' suffix.
    if input_filename.endswith(".json"):
        base_name = input_filename[:-5]
    else:
        base_name = input_filename
    output_filename = base_name + "-papers.json"
    
    # Read papers from the input file
    with open(input_filename, "r") as infile:
        papers_json = json.load(infile)
    
    for paper in papers_json:
        print(f"Processing paper: {paper['paper_title']}")
        pdf_url = paper["pdf_url"]
        
        # Step 1: Download the PDF
        pdf_stream = download_pdf(pdf_url)
        
        # Step 2: Extract text from the first 3 pages
        extracted_text = convert_pdf_to_markdown(pdf_stream, num_pages=3)
        if not extracted_text.strip():
            print("No text extracted from the first 3 pages.")
            continue
        
        # Step 3: Summarize the paper's goal using the OpenAI API
        summary = summarize_paper_goal(extracted_text)
        print(f"\nPaper Title: {paper['paper_title']}")
        print("Summary of the paper's goal:")
        print(summary)
        print("-" * 80)
        paper["paper_content"] = summary

    # Save the updated papers to the output file
    with open(output_filename, "w") as outfile:
        json.dump(papers_json, outfile, indent=2)
    print(f"Updated file saved as: {output_filename}")

if __name__ == "__main__":
    main()
