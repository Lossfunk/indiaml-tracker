import json
import re
import time
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize OpenAI client (ensure OPENAI_API_KEY is set in your environment)
client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY", "sk-or-v1-..."),
    base_url="https://openrouter.ai/api/v1",
)


# --- Input Data (as provided) ---
input_path = sys.argv[1]
papers_data = json.loads(open(input_path).read())

# --- Function to call LLM for selecting the most relevant Twitter/X link ---
def get_most_relevant_twitter_link_via_llm(author_name: str, paper_title: str, potential_links: list[str]) -> str:
    prompt = (
        f"You are a helpful assistant. From the following list of URLs found on the homepage of author '{author_name}' (author of '{paper_title}'), "
        f"identify the single most likely personal or professional Twitter or X profile URL. "
        f"If none seem personal/professional, respond with 'None'.\n\n"
        f"URLs:\n" + "\n".join(potential_links)
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that selects personal/professional social media profiles."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=64,
    )
    text = response.choices[0].message.content.strip()
    # If model returns a URL directly, use it; otherwise fallback to first
    if text.startswith("http"):
        return text
    else:
        return potential_links[0] if potential_links else ""

# --- Main Script Logic ---
results = {}
processed_urls = set()

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/91.0.4472.124 Safari/537.36',
        java_script_enabled=True
    )
    context.set_default_navigation_timeout(30000)
    context.set_default_timeout(15000)

    for paper in papers_data:
        paper_title = paper.get("paper_title", "Unknown Title")
        for author in paper.get("authors", []):
            author_name = author.get("name") or author.get("openreview_id", "Unknown Author")
            author_id = author.get("openreview_id", author_name)
            homepage_url = author.get("links", {}).get("homepage")

            if not homepage_url or homepage_url in processed_urls:
                author["twitter_handle_url"] = None
                author["status"] = "No homepage or already processed"
                continue

            processed_urls.add(homepage_url)
            page = None
            try:
                page = context.new_page()
                page.goto(homepage_url, wait_until='domcontentloaded')
                time.sleep(2)

                link_elements = page.locator('a[href*="twitter.com/"], a[href*="x.com/"]')
                potential_links = []
                for i in range(link_elements.count()):
                    href = link_elements.nth(i).get_attribute('href') or ''
                    if re.match(r'^https?:\/\/(?:www\.)?(twitter|x)\.com\/(?!home|explore|search|intent|share|i\/events|settings|notifications|messages|compose|tos|privacy|jobs|about|download|account|help|signup|login|i\/flow|lists)[a-zA-Z0-9_]{1,15}(?:\?.*|\/.*)?$', href, re.IGNORECASE):
                        href_norm = href.rstrip('/')
                        if href_norm not in potential_links:
                            potential_links.append(href_norm)

                if not potential_links:
                    author["twitter_handle_url"] = None
                    author["status"] = "No handle found"
                elif len(potential_links) == 1:
                    author["twitter_handle_url"] = potential_links[0]
                    author["status"] = "Handle found"
                else:
                    selected = get_most_relevant_twitter_link_via_llm(author_name, paper_title, potential_links)
                    author["twitter_handle_url"] = selected
                    author["status"] = "Handle selected via LLM"

            except PlaywrightTimeoutError:
                author["twitter_handle_url"] = None
                author["status"] = "Error: Timeout accessing homepage"
            except PlaywrightError as e:
                author["twitter_handle_url"] = None
                author["status"] = f"Error: Playwright {type(e).__name__}"
            except Exception as e:
                author["twitter_handle_url"] = None
                author["status"] = f"Error: {type(e).__name__}"
            finally:
                if page and not page.is_closed():
                    page.close()

    browser.close()

# --- Save Updated Data ---
output_path = input_path.replace('.json', '_with_twitter.json')
with open(output_path, 'w') as f:
    json.dump(papers_data, f, indent=2)

print(f"Updated data saved to {output_path}")
