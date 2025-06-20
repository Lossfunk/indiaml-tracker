from openai import OpenAI
import os
from dotenv import load_dotenv
import orjson

load_dotenv()


client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY", "sk-or-v1-..."),
    base_url="https://openrouter.ai/api/v1",
)

exa_client = OpenAI(
    api_key=os.environ.get("EXA_API_KEY", "nokey"),
    base_url="https://api.exa.ai",
)



SYSPROMPT = (
    """
You are an expert at understanding and extracting institute information from text.
Occasionally, the text may contain multiple institutes, and you should extract all of them, and try to resolve the acronyms to full names.
if you don't know the full name of an institute, you can use the acronym as is, but try to resolve it to the full name if possible.
if you don't know any field, you can leave it empty, but try to fill in as much information as possible.



Respond in JSON in the following format:
[{
    "institute_name": "Name of the institute, respond with the full name, not an acronym",
    "location": "City, State, Country",
    "website": "URL of the institute's website",
    "type": "academic/corporate/government",
    "country": "Country of the institute", infer from location if not provided, must be 2 letter ISO code (e.g., IN for India, US for United States)",
}]
"""
).strip()


def extract_institute_data(prompt: str) -> str:
    """
    Extracts institute information from a given prompt using OpenAI's Gemini model.

    Args:
        prompt (str): The input text containing institute information.

    Returns:
        str: The extracted institute information.
    """

    # Ensure the prompt is not empty
    if not prompt.strip():
        return "No institute information provided."

    response = client.chat.completions.create(
        model="google/gemini-2.5-flash-lite-preview-06-17",
        messages=[
            {
                "role": "system",
                "content": SYSPROMPT,
            },
            {"role": "user", "content": f"Extract the institute information from this text: {prompt}"},
        ],
        temperature=0.0,
        logprobs=True,
        max_tokens=512,
        response_format={
            "type": "json_object",
        },
        
    )

    response_content = orjson.loads(response.choices[0].message.content.strip())

    return response_content


def hydrate_institute_data(institute_data: list) -> list:
    """
    Hydrates the institute data with additional information.

    Args:
        institute_data (list): List of institute data dictionaries.

    Returns:
        list: List of hydrated institute data dictionaries.
    """
    for institute in institute_data:
        # Add default values or additional processing if needed
        institute.setdefault("website", "")
        institute.setdefault("type", "")
        institute.setdefault("country", "IN")  # Default to India if not provided
    return institute_data



if __name__ == "__main__":
    CHALLENGING_EXAMPLES = [
        {
            "case": "Ambiguous Acronyms",
            "input": "MIT researchers collaborated with MIT (Manipal Institute of Technology) on this project.",
            "why_challenging": "Same acronym, completely different institutes",
            "expected_count": 2
        },
        {
            "case": "Colloquial References",
            "input": "The folks at Big Blue and the nerds from Stanford worked together.",
            "why_challenging": "Requires knowing that 'Big Blue' = IBM",
            "expected_count": 2
        },
        {
            "case": "Informal Context Clues",
            "input": "The team from 1 Hacker Way (you know, Meta's headquarters) and the researchers at Building 40 (Google's AI building).",
            "why_challenging": "Requires inferring organizations from address/building references",
            "expected_count": 2
        },
        {
            "case": "Historical vs Current Names",
            "input": "Facebook Research (now Meta AI) and Google Brain (now part of Google DeepMind).",
            "why_challenging": "Must map old names to current organizations",
            "expected_count": 2
        },
        {
            "case": "Emoji and Symbol References",
            "input": "The people at 🍎 (Apple) and the team at 🐦 (Twitter, now X).",
            "why_challenging": "Emoji-based references with corporate name changes",
            "expected_count": 2
        },
        {
            "case": "Highly Ambiguous Acronyms",
            "input": "UW (could be University of Washington or University of Wisconsin) and UM (Michigan or Miami?).",
            "why_challenging": "Multiple valid interpretations for each acronym",
            "expected_count": 2
        },
        {
            "case": "Mixed Languages",
            "input": "ETH Zürich, École Polytechnique, and Universidad de Barcelona collaborated.",
            "why_challenging": "Non-English names requiring translation/recognition",
            "expected_count": 3
        },
        {
            "case": "Nested Corporate Structure",
            "input": "Google's DeepMind division and OpenAI's safety team worked on this.",
            "why_challenging": "Understanding parent-subsidiary relationships",
            "expected_count": 2
        },
        {
            "case": "Partial Information with Context",
            "input": "The university in Cambridge (the British one), Tokyo's top tech university, and the engineering school in Zurich.",
            "why_challenging": "Requires inferring specific institutions from descriptive clues",
            "expected_count": 3
        },
        {
            "case": "Numbers and Special Characters",
            "input": "42.fr (École 42), 3M Company, and the 2σ (Two Sigma) quantitative research team.",
            "why_challenging": "Non-standard naming with numbers and symbols",
            "expected_count": 3
        },
        {
            "case": "Typos and Misspellings",
            "input": "Standford University, Carneigie Mellon, and Masachusetts Institute of Technology.",
            "why_challenging": "Must recognize organizations despite spelling errors",
            "expected_count": 3
        },
        {
            "case": "Regional Groupings",
            "input": "Silicon Valley labs, Boston biotech firms, and Austin tech companies contributed.",
            "why_challenging": "Vague regional references without specific organization names",
            "expected_count": 0  # Should extract no specific institutes
        }
    ]

    def test_challenging_cases():
        """Test your extraction function on the most challenging cases."""
        print("Testing Most Challenging Cases")
        print("=" * 50)
        
        for i, example in enumerate(CHALLENGING_EXAMPLES, 1):
            print(f"\n{i}. {example['case']}")
            print(f"Input: {example['input']}")
            print(f"Why challenging: {example['why_challenging']}")
            print(f"Expected count: {example['expected_count']}")
            
            # Test with your function
            try:
                result = extract_institute_data(example['input'])
                print(f"Extracted count: {len(result)}")
                print("Extracted institutes:")
                for inst in result:
                    name = inst.get('institute_name', 'Unknown')
                    location = inst.get('location', 'Unknown')
                    print(f"  - {name} ({location})")
            except Exception as e:
                print(f"Error: {e}")
            
            print("-" * 30)

    def run_mini_benchmark():
        """Run a quick benchmark on just the challenging cases."""
        print("\nRunning Mini-Benchmark on Challenging Cases")
        print("=" * 50)
        
        total_cases = len(CHALLENGING_EXAMPLES)
        correct_count = 0
        partial_count = 0
        
        for example in CHALLENGING_EXAMPLES:
            try:
                result = extract_institute_data(example['input'])
                extracted_count = len(result)
                expected_count = example['expected_count']
                
                if extracted_count == expected_count:
                    correct_count += 1
                    status = "✓ CORRECT"
                elif extracted_count > 0 and expected_count > 0:
                    partial_count += 1
                    status = "~ PARTIAL"
                else:
                    status = "✗ FAILED"
                
                print(f"{example['case']:<25} | Expected: {expected_count} | Got: {extracted_count} | {status}")
                
            except Exception as e:
                print(f"{example['case']:<25} | ERROR: {str(e)[:50]}...")
        
        print("\n" + "=" * 50)
        print(f"Summary: {correct_count}/{total_cases} correct, {partial_count} partial")
        accuracy = correct_count / total_cases
        print(f"Accuracy: {accuracy:.2%}")

    # Quick performance categories for analysis
    PERFORMANCE_CATEGORIES = {
        "easy": ["medical", "gaming", "think_tanks"],
        "medium": ["government_agencies", "financial", "automotive", "consulting"],
        "hard": ["ambiguous_acronyms", "mixed_languages", "nested_organizations"],
        "very_hard": ["informal_context", "typos", "partial_info", "highly_ambiguous"]
    }

    def expected_performance_by_category():
        """Show expected performance ranges by category difficulty."""
        print("\nExpected Performance by Category Difficulty")
        print("=" * 50)
        
        for difficulty, categories in PERFORMANCE_CATEGORIES.items():
            print(f"\n{difficulty.upper()} Categories:")
            print(f"  Categories: {', '.join(categories)}")
            
            if difficulty == "easy":
                print("  Expected F1 Score: 0.85-0.95")
                print("  Expected Exact Match: 0.80-0.90")
            elif difficulty == "medium":
                print("  Expected F1 Score: 0.70-0.85")
                print("  Expected Exact Match: 0.60-0.80")
            elif difficulty == "hard":
                print("  Expected F1 Score: 0.50-0.70")
                print("  Expected Exact Match: 0.40-0.60")
            elif difficulty == "very_hard":
                print("  Expected F1 Score: 0.30-0.50")
                print("  Expected Exact Match: 0.20-0.40")




    print("Institute Extraction Benchmark Integration")
    print("=" * 50)
    
    # Test individual challenging cases
    test_challenging_cases()
    
    # Run mini benchmark
    run_mini_benchmark()
    
    # Show performance expectations
    expected_performance_by_category()
    
    print("\n" + "=" * 50)
    print("To run the full benchmark:")
    print("1. Load the benchmark: benchmark_data = load_benchmark_data()")
    print("2. Run: results = run_comprehensive_benchmark(extract_institute_data)")
    print("3. View: print_benchmark_report(results)")
    print("4. Save: save_results(results)")