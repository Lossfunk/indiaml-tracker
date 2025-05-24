import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
import re
import time
import json
import sys

# --- Input Data (as provided) ---
papers_data = json.loads(open(sys.argv[1]).read())


# --- Function to simulate LLM call (replace with actual API call) ---
def get_most_relevant_twitter_link_via_llm(author_name, paper_title, potential_links):
    """
    Placeholder function to simulate LLM selection.
    In a real scenario, this would involve calling an LLM API (e.g., Gemini).
    For now, it just returns the first link as a placeholder.
    """
    print(f"--- LLM SIMULATION ---")
    print(f"Author: {author_name}")
    print(f"Paper: {paper_title}")
    print(f"Potential Links: {potential_links}")
    # Construct prompt for LLM:
    # prompt = f"From the following list of URLs found on the homepage of author '{author_name}' (author of '{paper_title}'), please identify the most likely personal or professional Twitter/X handle URL: {', '.join(potential_links)}. Only return the single most relevant URL."
    # response = call_llm_api(prompt) # Replace with actual API call
    # selected_link = parse_llm_response(response) # Extract URL from response
    selected_link = potential_links[0] # Placeholder: just take the first one
    print(f"LLM Simulation selected: {selected_link}")
    print(f"----------------------")
    return selected_link

# --- Main Script Logic ---
results = {}
processed_urls = set() # To avoid scraping the same homepage multiple times if an author appears in multiple papers

with sync_playwright() as p:
    browser = p.chromium.launch()
    # Set a default timeout for navigation and actions
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        java_script_enabled=True # Ensure JS is enabled as some sites render links dynamically
    )
    context.set_default_navigation_timeout(30000) # 30 seconds navigation timeout
    context.set_default_timeout(15000) # 15 seconds action timeout

    for i, paper in enumerate(papers_data):
        paper_title = paper.get("paper_title", f"Paper {i+1}")
        print(f"\nProcessing Paper: {paper_title}")
        authors = paper.get("authors", [])

        for author in authors:
            author_name = author.get("name") or author.get("openreview_id", "Unknown Author")
            author_id = author.get("openreview_id", author_name) # Unique identifier
            links = author.get("links", {})
            homepage_url = links.get("homepage")

            if not homepage_url:
                print(f"  Skipping author '{author_name}': No homepage URL found.")
                continue

            # Skip if this exact URL was already processed
            if homepage_url in processed_urls:
                 print(f"  Skipping author '{author_name}': Homepage {homepage_url} already processed.")
                 continue

            print(f"  Processing author '{author_name}' - Homepage: {homepage_url}")
            results[author_id] = {"name": author_name, "homepage": homepage_url, "twitter_handle_url": None, "status": "Processing"}
            processed_urls.add(homepage_url) # Mark URL as processed

            page = None # Initialize page variable
            try:
                page = context.new_page()
                page.goto(homepage_url, wait_until='domcontentloaded') # Wait for DOM, not full load
                time.sleep(2) # Give a little extra time for dynamic content if needed

                # Find potential Twitter/X links using CSS selectors
                # Looks for hrefs containing 'twitter.com/' or 'x.com/'
                # We look for the pattern to avoid matching general links to twitter.com without a username
                link_elements = page.locator('a[href*="twitter.com/"], a[href*="x.com/"]')

                potential_links = []
                count = link_elements.count()
                print(f"    Found {count} potential link elements.")

                for j in range(count):
                    try:
                        href = link_elements.nth(j).get_attribute('href')
                        if href:
                            # Basic validation: Check if it looks like a profile URL
                            # Exclude simple links like twitter.com/home, twitter.com/explore, etc.
                             # Regex explanation:
                             # ^https?:\/\/       : Starts with http:// or https://
                             # (?:www\.)?        : Optional www.
                             # (twitter|x)\.com\/: Matches twitter.com/ or x.com/
                             # (?!home|explore|search|intent|share|...) : Negative lookahead - ensures the path doesn't start with common non-profile paths
                             # [a-zA-Z0-9_]{1,15}: Matches a valid username (alphanumeric + underscore, 1-15 chars)
                             # (?:\?.*|\/.*)?$   : Optionally followed by query params or further path segments (like /status/...), or end of string
                             # We specifically look for profile patterns.
                            if re.match(r'^https?:\/\/(?:www\.)?(twitter|x)\.com\/(?!home|explore|search|intent|share|i\/events|settings|notifications|messages|compose|tos|privacy|jobs|about|download|account|help|signup|login|i\/flow|lists)[a-zA-Z0-9_]{1,15}(?:\?.*|\/.*)?$', href, re.IGNORECASE):
                                # Normalize URL slightly (optional, e.g., remove trailing slash)
                                normalized_href = href.rstrip('/')
                                if normalized_href not in potential_links:
                                     potential_links.append(normalized_href)
                    except PlaywrightError as e:
                         print(f"      Error getting attribute for link {j}: {e}")
                    except Exception as e: # Catch any other unexpected error
                         print(f"      Unexpected error processing link {j}: {e}")


                print(f"    Found valid potential Twitter/X profile links: {potential_links}")

                if not potential_links:
                    print(f"    No valid Twitter/X profile links found for {author_name}.")
                    results[author_id]["status"] = "No handle found"
                elif len(potential_links) == 1:
                    print(f"    Found single handle for {author_name}: {potential_links[0]}")
                    results[author_id]["twitter_handle_url"] = potential_links[0]
                    results[author_id]["status"] = "Handle found"
                else:
                    print(f"    Found multiple handles for {author_name}. Simulating LLM selection...")
                    # --- LLM Call Simulation ---
                    # In a real implementation, you would call your chosen LLM API here.
                    # Pass author_name, paper_title, and potential_links
                    # The LLM should be prompted to return the most likely *personal* or *professional* handle.
                    selected_link = get_most_relevant_twitter_link_via_llm(author_name, paper_title, potential_links)
                    results[author_id]["twitter_handle_url"] = selected_link
                    results[author_id]["status"] = "Handle selected via LLM (simulated)"

            except PlaywrightTimeoutError:
                print(f"    ERROR: Timeout navigating to or interacting with {homepage_url} for {author_name}")
                results[author_id]["status"] = f"Error: Timeout accessing homepage"
            except PlaywrightError as e:
                print(f"    ERROR: Playwright error for {author_name} at {homepage_url}: {e}")
                results[author_id]["status"] = f"Error: Playwright ({type(e).__name__})"
            except Exception as e:
                print(f"    ERROR: Unexpected error processing {author_name} at {homepage_url}: {e}")
                results[author_id]["status"] = f"Error: Unexpected ({type(e).__name__})"
            finally:
                if page and not page.is_closed():
                    page.close()

    browser.close()

# --- Output Results ---
print("\n\n--- Final Results ---")
print(json.dumps(results, indent=2))

# Example: Print only authors for whom a handle was found/selected
print("\n--- Authors with Found/Selected Twitter Handles ---")
for author_id, data in results.items():
    if data.get("twitter_handle_url"):
        print(f"- {data['name']} ({author_id}): {data['twitter_handle_url']}")