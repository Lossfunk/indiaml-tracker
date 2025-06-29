"""
Markdown Generator for Tweet Generation Pipeline

Generates markdown files from tweet thread JSON data.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from .state_manager import StateManager


class MarkdownGenerator:
    """Generates markdown documentation from tweet thread data."""
    
    def __init__(self, state_manager: StateManager, config: 'PipelineConfig'):
        self.state_manager = state_manager
        self.config = config
    
    def generate_markdown(self, tweet_thread: Dict[str, Any]) -> str:
        """Generate markdown from tweet thread JSON."""
        print("📝 Generating markdown from tweet thread...")
        
        # Check if already generated
        if self.state_manager.checkpoint_exists("tweet_thread.md"):
            print("  ✅ Markdown already generated, loading from checkpoint...")
            with open(self.state_manager.get_checkpoint_file("tweet_thread.md"), 'r', encoding='utf-8') as f:
                return f.read()
        
        markdown_content = self._generate_markdown_content(tweet_thread)
        
        # Save markdown file
        with open(self.state_manager.get_checkpoint_file("tweet_thread.md"), 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Also save to main output directory
        output_file = self.state_manager.conference_dir / "tweet_thread.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"  ✅ Markdown saved to {output_file}")
        return markdown_content
    
    def _generate_markdown_content(self, tweet_thread: Dict[str, Any]) -> str:
        """Generate the actual markdown content."""
        conference = tweet_thread["conference"]
        year = tweet_thread["year"]
        generated_at = tweet_thread["generated_at"]
        metadata = tweet_thread["metadata"]
        analytics = tweet_thread["analytics_summary"]
        tweets = tweet_thread["tweets"]
        
        # Start building markdown
        md = []
        
        # Header
        md.append(f"# India @ {conference} {year} Tweet Thread")
        md.append("")
        md.append(f"Generated on: {datetime.fromisoformat(generated_at).strftime('%B %d, %Y at %I:%M %p')}")
        md.append(f"Processing time: {metadata['processing_time']}")
        md.append("")
        
        # Analytics Overview
        md.append("## 📊 Analytics Overview")
        md.append("")
        md.append(f"- **Total Papers**: {analytics['india_papers']}")
        md.append(f"- **Global Rank**: #{analytics['global_rank']}")
        md.append(f"- **Acceptance Rate**: {analytics['acceptance_rate']}")
        md.append(f"- **APAC Rank**: #{analytics['apac_rank']}")
        md.append(f"- **US + China Combined**: {analytics['us_china_combined']}")
        md.append(f"- **Quality Papers**: {analytics['quality_papers']} (spotlights + orals)")
        md.append("")
        
        # Thread Statistics
        md.append("## 📈 Thread Statistics")
        md.append("")
        md.append(f"- **Total Tweets**: {metadata['total_tweets']}")
        md.append(f"- **Analytics Tweets**: {metadata['analytics_tweets']}")
        md.append(f"- **Paper Tweets**: {metadata['paper_tweets']}")
        md.append(f"- **Closing Tweets**: {metadata['closing_tweets']}")
        md.append(f"- **Total Papers Covered**: {metadata['total_papers']}")
        md.append(f"- **Total Authors**: {metadata['total_authors']}")
        md.append("")
        
        # Tweet Thread
        md.append("## 🧵 Tweet Thread")
        md.append("")
        
        for i, tweet in enumerate(tweets, 1):
            md.append(f"### Tweet {i} ({tweet['type'].title()})")
            md.append("")
            
            # Tweet content
            md.append("```")
            md.append(tweet['content'])
            md.append("```")
            md.append("")
            
            # Tweet metadata
            md.append("**Metadata:**")
            md.append(f"- Character count: {tweet['metadata']['character_count']}")
            md.append(f"- Created at: {datetime.fromisoformat(tweet['metadata']['created_at']).strftime('%I:%M:%S %p')}")
            
            if tweet['mentions']:
                md.append(f"- Mentions: {', '.join(tweet['mentions'])}")
            
            if tweet['hashtags']:
                md.append(f"- Hashtags: {', '.join(tweet['hashtags'])}")
            
            # Paper-specific metadata
            if tweet['type'] == 'paper':
                md.append(f"- Paper ID: `{tweet['paper_id']}`")
                md.append(f"- Authors: {tweet['metadata']['author_count']}")
                md.append(f"- Mentions: {tweet['metadata']['mentions_count']}")
                
                if tweet['metadata']['is_spotlight']:
                    md.append("- **🌟 Spotlight Paper**")
                if tweet['metadata']['is_oral']:
                    md.append("- **🎤 Oral Presentation**")
                
                # Author details
                if tweet.get('authors'):
                    md.append("")
                    md.append("**Authors:**")
                    for author in tweet['authors']:
                        author_line = f"- {author['name']}"
                        if author['affiliation']:
                            author_line += f" ({author['affiliation']})"
                        if author['twitter_handle']:
                            author_line += f" - {author['twitter_handle']}"
                        md.append(author_line)
            
            md.append("")
            md.append("---")
            md.append("")
        
        # Paper Index
        md.append("## 📄 Paper Index")
        md.append("")
        
        paper_tweets = [t for t in tweets if t['type'] == 'paper']
        
        for i, tweet in enumerate(paper_tweets, 1):
            paper_title = self._extract_title_from_content(tweet['content'])
            quality_indicators = []
            
            if tweet['metadata']['is_spotlight']:
                quality_indicators.append("🌟")
            if tweet['metadata']['is_oral']:
                quality_indicators.append("🎤")
            
            quality_text = " ".join(quality_indicators)
            if quality_text:
                quality_text = f" {quality_text}"
            
            md.append(f"{i}. **{paper_title}**{quality_text}")
            
            # First author and institution
            if tweet.get('authors') and tweet['authors']:
                first_author = tweet['authors'][0]
                author_info = first_author['name']
                if first_author['affiliation']:
                    author_info += f" ({first_author['affiliation']})"
                md.append(f"   - {author_info}")
            
            md.append(f"   - Paper ID: `{tweet['paper_id']}`")
            md.append("")
        
        # Author Index
        md.append("## 👥 Author Index")
        md.append("")
        
        # Collect all unique authors
        all_authors = {}
        for tweet in paper_tweets:
            if tweet.get('authors'):
                for author in tweet['authors']:
                    author_id = f"{author['name']}_{author['affiliation']}"
                    if author_id not in all_authors:
                        all_authors[author_id] = author
        
        # Sort authors by name
        sorted_authors = sorted(all_authors.values(), key=lambda x: x['name'])
        
        for author in sorted_authors:
            author_line = f"- **{author['name']}**"
            if author['affiliation']:
                author_line += f" - {author['affiliation']}"
            
            links = []
            if author['twitter_handle']:
                links.append(f"[Twitter]({author['twitter_url']})")
            if author['google_scholar']:
                links.append(f"[Scholar]({author['google_scholar']})")
            if author['linkedin']:
                links.append(f"[LinkedIn]({author['linkedin']})")
            
            if links:
                author_line += f" - {' | '.join(links)}"
            
            md.append(author_line)
        
        md.append("")
        
        # Footer
        md.append("---")
        md.append("")
        md.append("*Generated by India@ML Tweet Generation Pipeline*")
        md.append("")
        md.append(f"Conference: {conference} {year}")
        md.append(f"Generated: {datetime.fromisoformat(generated_at).strftime('%B %d, %Y')}")
        
        return "\n".join(md)
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract paper title from tweet content."""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('📄 '):
                return line[2:].strip()
        return "Unknown Title"
    
    def generate_summary_markdown(self, tweet_thread: Dict[str, Any]) -> str:
        """Generate a summary markdown file."""
        conference = tweet_thread["conference"]
        year = tweet_thread["year"]
        analytics = tweet_thread["analytics_summary"]
        metadata = tweet_thread["metadata"]
        
        summary_md = []
        
        # Header
        summary_md.append(f"# India @ {conference} {year} - Summary")
        summary_md.append("")
        
        # Key Statistics
        summary_md.append("## Key Statistics")
        summary_md.append("")
        summary_md.append(f"🇮🇳 **India's Performance:**")
        summary_md.append(f"- {analytics['india_papers']} papers accepted")
        summary_md.append(f"- Ranked #{analytics['global_rank']} globally")
        summary_md.append(f"- {analytics['acceptance_rate']} of total papers")
        summary_md.append(f"- Ranked #{analytics['apac_rank']} in APAC region")
        summary_md.append("")
        
        summary_md.append(f"🌟 **Quality Highlights:**")
        summary_md.append(f"- {analytics['quality_papers']} high-quality papers (spotlights + orals)")
        summary_md.append("")
        
        summary_md.append(f"🌍 **Global Context:**")
        summary_md.append(f"- US + China combined: {analytics['us_china_combined']} of papers")
        summary_md.append("")
        
        # Thread Information
        summary_md.append("## Thread Information")
        summary_md.append("")
        summary_md.append(f"- **Total Tweets**: {metadata['total_tweets']}")
        summary_md.append(f"- **Papers Covered**: {metadata['total_papers']}")
        summary_md.append(f"- **Authors Featured**: {metadata['total_authors']}")
        summary_md.append(f"- **Processing Time**: {metadata['processing_time']}")
        summary_md.append("")
        
        # Save summary
        summary_file = self.state_manager.conference_dir / "summary.md"
        summary_content = "\n".join(summary_md)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"  ✅ Summary saved to {summary_file}")
        return summary_content
