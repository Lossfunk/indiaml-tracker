#!/usr/bin/env python3
import argparse
import pathlib
from google import genai
from dotenv import load_dotenv
load_dotenv()


def summarize_paper(pdf_path: pathlib.Path, client: genai.Client, model: str, prompt: str) -> str:
    """
    Uploads a PDF to the File API and generates a tight bullet-point summary.
    """
    # Upload the PDF (large files use the File API)
    uploaded = client.files.upload(
        file=pdf_path,
        config=dict(mime_type='application/pdf')
    )
    # Generate the summary
    response = client.models.generate_content(
        model=model,
        contents=[uploaded, prompt]
    )
    return response.text




def main():
    parser = argparse.ArgumentParser(
        description="Summarize PDF papers into ≤20-bullet lists of claim, method, results, limitations, reproducibility."
    )
    parser.add_argument(
        'pdfs',
        nargs='+',
        type=pathlib.Path,
        help="Paths to one or more PDF files"
    )
    parser.add_argument(
        '--model',
        default='gemini-2.5-pro-preview',
        help="Gemini model to use (e.g. gemini-2.5-pro-preview or gemini-2.0-flash)"
    )
    args = parser.parse_args()

    client = genai.Client()
    prompt = (
       "You’ve just ingested a PDF of a research paper. Produce a structured summary of up to 30 bullets (ideally ~28) to help us evaluate its corporate differentiability potential. Do not draw on any knowledge outside the PDF itself—the only allowed ‘external’ context is prior work and citations explicitly discussed within the paper. Organize your bullets under these headings, with the suggested bullet-count ranges:"
        "Context & Related Work (1–2 bullets)"
        "Summarize how the paper positions itself against prior art as described in the text and references."
        "Core Claims (3–5 bullets)"
        "List the novel hypotheses or contributions the authors assert."
        "Methodology (5–6 bullets)"
        "Describe the architectures, algorithms, datasets, hyperparameters, and implementation details presented in the paper."
        "Results & Metrics (5–6 bullets)"
        "Report the quantitative outcomes, benchmarks, baselines, and ablation studies shown in the figures/tables."
        "Limitations & Risks (3–4 bullets)"
        "Note any assumptions, failure modes, scalability issues, or ethical/regulatory concerns acknowledged by the authors."
        "Reproducibility (2–3 bullets)"
        "State the availability of code/data, clarity of protocols, and compute requirements as specified in the paper."
        "Corporate Differentiability (5–6 bullets)"
        "Identify potential for defensible IP or patents based solely on the paper’s content."
        "Highlight gaps versus competitors as the authors describe them."
        "Outline integration or productization pathways and strategic risks inferred strictly from the paper."
        "Mention any adjacent capabilities or spin-off opportunities mentioned by the authors."
        "Keep each bullet concise and precise, focusing only on information and insights explicitly contained in the PDF, to inform whether and how our company might leverage or extend this work for strategic advantage."
    )

    for pdf_path in args.pdfs:
        if not pdf_path.is_file():
            print(f"Error: {pdf_path} not found or is not a file.")
            continue

        print(f"\n=== Summarizing: {pdf_path.name} ===\n")
        summary = summarize_paper(pdf_path, client, args.model, prompt)
        print(summary)
        print("-" * 60)

if __name__ == '__main__':
    main()
