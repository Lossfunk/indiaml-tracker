"""
Author Enricher for Tweet Generation Pipeline

Enriches author data with social media links and additional profile information.
Extends the existing Twitter handle finder with additional profile discovery.
"""

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from openai import OpenAI
from dotenv import load_dotenv
import os
from .state_manager import StateManager

load_dotenv()


class AuthorEnricher:
    """Enriches author data with social media profiles."""
    
    def __init__(self, state_manager: StateManager, config: 'PipelineConfig'):
        self.state_manager = state_manager
        self.config = config
        self.max_concurrent = config.max_concurrent_requests
        self.timeout = config.request_timeout * 1000  # Convert to milliseconds
        self.processed_urls: Set[str] = set()
        
        # Initialize OpenAI client for profile verification
        try:
            self.client = OpenAI(
                api_key=os.environ.get("OPENROUTER_API_KEY", os.environ.get("OPENAI_API_KEY")),
                base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            )
        except Exception:
            self.client = None
            print("⚠️  Warning: No OpenAI/OpenRouter API key found. Profile verification will be basic.")
        
        self.stats = {
            'total_authors': 0,
            'processed_authors': 0,
            'twitter_found': 0,
            'scholar_found': 0,
            'linkedin_found': 0,
            'no_homepage': 0,
            'errors': 0,
            'skipped': 0
        }
    
    async def enrich_authors(self, authors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich all authors with social media and academic profile links."""
        print(f"🔍 Starting author enrichment for {len(authors)} authors...")
        
        # Load existing progress
        progress = self.state_manager.load_checkpoint("enrichment_progress.json") or {}
        enriched_authors = []
        
        self.stats['total_authors'] = len(authors)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True
            )
            
            context.set_default_navigation_timeout(self.timeout)
            context.set_default_timeout(15000)
            
            # Process authors in batches
            for i in range(0, len(authors), self.max_concurrent):
                batch = authors[i:i + self.max_concurrent]
                
                # Process batch concurrently
                tasks = []
                for author in batch:
                    author_id = str(author["id"])
                    
                    # Check if already processed
                    if author_id in progress and progress[author_id].get("status") == "completed":
                        print(f"  ⏭️  Skipping {author['full_name']} (already processed)")
                        enriched_author = author.copy()
                        enriched_author.update(progress[author_id]["data"])
                        enriched_authors.append(enriched_author)
                        self.stats['skipped'] += 1
                        continue
                    
                    task = self._enrich_single_author(context, author, progress)
                    tasks.append(task)
                
                # Wait for batch to complete
                if tasks:
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in batch_results:
                        if isinstance(result, Exception):
                            print(f"  ❌ Batch error: {result}")
                            self.stats['errors'] += 1
                        else:
                            enriched_authors.append(result)
                    
                    # Save progress after each batch
                    self._save_progress(progress)
                    
                    # Rate limiting between batches
                    if i + self.max_concurrent < len(authors):
                        await asyncio.sleep(2)
            
            await browser.close()
        
        # Final save
        self.state_manager.save_checkpoint("enriched_authors.json", enriched_authors)
        self._save_progress(progress)
        
        self._print_statistics()
        return enriched_authors
    
    async def _enrich_single_author(self, context, author: Dict[str, Any], progress: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single author's profile."""
        author_id = str(author["id"])
        author_name = author.get("full_name", "Unknown Author")
        
        print(f"  🔍 Processing: {author_name}")
        
        # Initialize enriched author data
        enriched_author = author.copy()
        enrichment_data = {
            "twitter_handle": None,
            "twitter_url": None,
            "google_scholar_verified": author.get("google_scholar_link"),
            "linkedin_verified": author.get("linkedin"),
            "additional_profiles": {},
            "enrichment_status": "no_homepage",
            "processed_at": time.time()
        }
        
        homepage_url = author.get("homepage")
        
        if not homepage_url or homepage_url in self.processed_urls:
            if homepage_url in self.processed_urls:
                enrichment_data["enrichment_status"] = "already_processed"
            else:
                self.stats['no_homepage'] += 1
        else:
            self.processed_urls.add(homepage_url)
            
            try:
                # Extract profiles from homepage
                profiles = await self._extract_profiles_from_homepage(context, homepage_url, author_name)
                enrichment_data.update(profiles)
                enrichment_data["enrichment_status"] = "completed"
                
                # Update statistics
                if profiles.get("twitter_url"):
                    self.stats['twitter_found'] += 1
                if profiles.get("google_scholar_verified"):
                    self.stats['scholar_found'] += 1
                if profiles.get("linkedin_verified"):
                    self.stats['linkedin_found'] += 1
                    
            except Exception as e:
                print(f"    ❌ Error processing {author_name}: {e}")
                enrichment_data["enrichment_status"] = f"error: {str(e)}"
                self.stats['errors'] += 1
        
        # Update author with enriched data
        enriched_author.update(enrichment_data)
        
        # Save individual progress
        progress[author_id] = {
            "status": "completed",
            "data": enrichment_data,
            "processed_at": time.time()
        }
        
        self.stats['processed_authors'] += 1
        return enriched_author
    
    async def _extract_profiles_from_homepage(self, context, homepage_url: str, author_name: str) -> Dict[str, Any]:
        """Extract social media and academic profiles from author's homepage."""
        page = None
        profiles = {
            "twitter_handle": None,
            "twitter_url": None,
            "google_scholar_verified": None,
            "linkedin_verified": None,
            "additional_profiles": {}
        }
        
        try:
            page = await context.new_page()
            await page.goto(homepage_url, wait_until='domcontentloaded')
            await page.wait_for_timeout(2000)
            
            html_content = await page.content()
            
            # Extract Twitter/X links
            twitter_links = self._extract_twitter_links(html_content)
            if twitter_links:
                if len(twitter_links) == 1:
                    profiles["twitter_url"] = twitter_links[0]
                    profiles["twitter_handle"] = self._extract_handle_from_url(twitter_links[0])
                    print(f"    🐦 Found Twitter: {twitter_links[0]}")
                else:
                    # Use LLM to select best match
                    selected = await self._select_best_twitter_profile(author_name, twitter_links)
                    if selected:
                        profiles["twitter_url"] = selected
                        profiles["twitter_handle"] = self._extract_handle_from_url(selected)
                        print(f"    🤖 Selected Twitter: {selected}")
            
            # Extract Google Scholar links
            scholar_links = self._extract_google_scholar_links(html_content)
            if scholar_links:
                profiles["google_scholar_verified"] = scholar_links[0]
                print(f"    🎓 Found Scholar: {scholar_links[0]}")
            
            # Extract LinkedIn links
            linkedin_links = self._extract_linkedin_links(html_content)
            if linkedin_links:
                profiles["linkedin_verified"] = linkedin_links[0]
                print(f"    💼 Found LinkedIn: {linkedin_links[0]}")
            
            # Extract additional profiles
            additional = self._extract_additional_profiles(html_content)
            if additional:
                profiles["additional_profiles"] = additional
                print(f"    🔗 Found additional profiles: {list(additional.keys())}")
            
        finally:
            if page and not page.is_closed():
                await page.close()
        
        return profiles
    
    def _extract_twitter_links(self, html_content: str) -> List[str]:
        """Extract Twitter/X links from HTML content."""
        twitter_pattern = r'https?:\/\/(?:www\.)?(twitter|x)\.com\/(?!home|explore|search|intent|share|i\/events|settings|notifications|messages|compose|tos|privacy|jobs|about|download|account|help|signup|login|i\/flow|lists)([a-zA-Z0-9_]{1,15})(?:\?.*|\/.*)?'
        
        potential_links = []
        matches = re.finditer(twitter_pattern, html_content, re.IGNORECASE)
        
        for match in matches:
            url = match.group(0).rstrip('/').replace('twitter.com/', 'x.com/')
            if url not in potential_links:
                potential_links.append(url)
        
        return potential_links
    
    def _extract_google_scholar_links(self, html_content: str) -> List[str]:
        """Extract Google Scholar links from HTML content."""
        scholar_pattern = r'https?:\/\/scholar\.google\.com\/citations\?user=([a-zA-Z0-9_-]+)'
        
        matches = re.finditer(scholar_pattern, html_content, re.IGNORECASE)
        links = []
        
        for match in matches:
            url = match.group(0)
            if url not in links:
                links.append(url)
        
        return links
    
    def _extract_linkedin_links(self, html_content: str) -> List[str]:
        """Extract LinkedIn links from HTML content."""
        linkedin_pattern = r'https?:\/\/(?:www\.)?linkedin\.com\/in\/([a-zA-Z0-9_-]+)'
        
        matches = re.finditer(linkedin_pattern, html_content, re.IGNORECASE)
        links = []
        
        for match in matches:
            url = match.group(0)
            if url not in links:
                links.append(url)
        
        return links
    
    def _extract_additional_profiles(self, html_content: str) -> Dict[str, str]:
        """Extract additional academic and professional profiles."""
        profiles = {}
        
        # ORCID
        orcid_pattern = r'https?:\/\/orcid\.org\/([0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X])'
        orcid_matches = re.finditer(orcid_pattern, html_content, re.IGNORECASE)
        for match in orcid_matches:
            profiles["orcid"] = match.group(0)
            break
        
        # ResearchGate
        rg_pattern = r'https?:\/\/(?:www\.)?researchgate\.net\/profile\/([a-zA-Z0-9_-]+)'
        rg_matches = re.finditer(rg_pattern, html_content, re.IGNORECASE)
        for match in rg_matches:
            profiles["researchgate"] = match.group(0)
            break
        
        # GitHub
        github_pattern = r'https?:\/\/(?:www\.)?github\.com\/([a-zA-Z0-9_-]+)(?:\/|$)'
        github_matches = re.finditer(github_pattern, html_content, re.IGNORECASE)
        for match in github_matches:
            profiles["github"] = match.group(0)
            break
        
        return profiles
    
    def _extract_handle_from_url(self, twitter_url: str) -> str:
        """Extract Twitter handle from URL."""
        match = re.search(r'(?:twitter|x)\.com\/([a-zA-Z0-9_]+)', twitter_url)
        if match:
            return f"@{match.group(1)}"
        return ""
    
    async def _select_best_twitter_profile(self, author_name: str, twitter_links: List[str]) -> Optional[str]:
        """Use LLM to select the most relevant Twitter profile."""
        if not self.client or not twitter_links:
            return twitter_links[0] if twitter_links else None
        
        prompt = (
            f"From the following Twitter/X URLs found on '{author_name}'s homepage, "
            f"select the most likely personal/professional profile for this academic researcher. "
            f"Respond with just the URL or 'None'.\n\n"
            + "\n".join(f"- {link}" for link in twitter_links)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=os.environ.get("OPENROUTER_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "Select personal/professional Twitter profiles for academic researchers. Respond with just the URL or 'None'."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=128,
            )
            text = response.choices[0].message.content.strip()
            
            if text.startswith("http"):
                return text
            elif text.lower() == 'none':
                return None
            else:
                return twitter_links[0] if twitter_links else None
                
        except Exception as e:
            print(f"    ⚠️  LLM selection failed: {e}")
            return twitter_links[0] if twitter_links else None
    
    def _save_progress(self, progress: Dict[str, Any]) -> None:
        """Save enrichment progress."""
        self.state_manager.save_checkpoint("enrichment_progress.json", progress)
        
        # Update state manager progress
        self.state_manager.update_progress(
            processed_authors=self.stats['processed_authors'],
            enriched_authors=self.stats['processed_authors']
        )
    
    def _print_statistics(self) -> None:
        """Print enrichment statistics."""
        print(f"\n🔍 Author Enrichment Summary:")
        print(f"  📊 Total authors: {self.stats['total_authors']}")
        print(f"  ✅ Processed: {self.stats['processed_authors']}")
        print(f"  ⏭️  Skipped: {self.stats['skipped']}")
        print(f"  🐦 Twitter found: {self.stats['twitter_found']}")
        print(f"  🎓 Scholar found: {self.stats['scholar_found']}")
        print(f"  💼 LinkedIn found: {self.stats['linkedin_found']}")
        print(f"  🏠 No homepage: {self.stats['no_homepage']}")
        print(f"  ❌ Errors: {self.stats['errors']}")
