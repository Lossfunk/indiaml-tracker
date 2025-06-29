"""
Tweet Generator for Tweet Generation Pipeline

Generates tweet thread content in JSON format with all metadata.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from .state_manager import StateManager


class TweetGenerator:
    """Generates tweets from enriched paper and author data."""
    
    def __init__(self, state_manager: StateManager, config: 'PipelineConfig'):
        self.state_manager = state_manager
        self.config = config
        self.tweet_counter = 0
        
        # Tweet configuration
        self.max_tweet_length = 280
        self.hashtags = ["#ICML2025", "#IndiaML", "#MachineLearning", "#Research"]
        
    def generate_tweet_thread(self, papers: List[Dict[str, Any]], enriched_authors: List[Dict[str, Any]], 
                            analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete tweet thread as JSON."""
        print(f"🐦 Generating tweet thread for {len(papers)} papers...")
        
        # Check if already generated
        if self.state_manager.checkpoint_exists("tweet_thread.json"):
            print("  ✅ Tweet thread already generated, loading from checkpoint...")
            return self.state_manager.load_checkpoint("tweet_thread.json")
        
        self.tweet_counter = 0
        tweets = []
        
        # Create author lookup for enriched data
        author_lookup = {str(author["id"]): author for author in enriched_authors}
        
        # 1. Generate opening analytics tweet
        opening_tweet = self._generate_opening_tweet(analytics)
        tweets.append(opening_tweet)
        
        # 2. Generate summary insights tweet
        summary_tweet = self._generate_summary_tweet(analytics)
        tweets.append(summary_tweet)
        
        # 3. Generate paper tweets
        paper_tweets = self._generate_paper_tweets(papers, author_lookup, analytics)
        tweets.extend(paper_tweets)
        
        # 4. Generate closing tweet
        closing_tweet = self._generate_closing_tweet(analytics, len(papers))
        tweets.append(closing_tweet)
        
        # Create thread metadata
        thread_data = {
            "conference": analytics["conference"]["name"],
            "year": analytics["conference"]["year"],
            "generated_at": datetime.now().isoformat(),
            "metadata": {
                "total_tweets": len(tweets),
                "analytics_tweets": 2,  # opening + summary
                "paper_tweets": len(paper_tweets),
                "closing_tweets": 1,
                "total_papers": len(papers),
                "total_authors": len(enriched_authors),
                "processing_time": self._calculate_processing_time()
            },
            "analytics_summary": {
                "india_papers": analytics["india_data"]["total_papers"],
                "global_rank": analytics["global_rankings"]["india_rank"],
                "acceptance_rate": f"{analytics['insights']['acceptance_rate']:.1f}%",
                "apac_rank": analytics["apac_rankings"]["india_rank"],
                "us_china_combined": f"{analytics['global_rankings']['us_cn_combined']['percentage']:.1f}%",
                "quality_papers": analytics["insights"]["quality_metrics"]["total_quality"]
            },
            "tweets": tweets
        }
        
        # Save checkpoint
        self.state_manager.save_checkpoint("tweet_thread.json", thread_data)
        
        print(f"  ✅ Generated {len(tweets)} tweets")
        return thread_data
    
    def _generate_opening_tweet(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate opening analytics tweet."""
        self.tweet_counter += 1
        
        content = analytics["insights"]["opening_tweet"]
        
        # Add hashtags
        hashtags_text = " ".join(self.hashtags[:3])  # Limit hashtags to fit
        if len(content + " " + hashtags_text) <= self.max_tweet_length:
            content += f"\n\n{hashtags_text}"
        
        return {
            "id": self.tweet_counter,
            "type": "analytics_opener",
            "content": content,
            "mentions": [],
            "hashtags": self.hashtags[:3],
            "metadata": {
                "character_count": len(content),
                "created_at": datetime.now().isoformat(),
                "analytics_data": {
                    "india_papers": analytics["india_data"]["total_papers"],
                    "global_rank": analytics["global_rankings"]["india_rank"],
                    "acceptance_rate": analytics["insights"]["acceptance_rate"]
                }
            }
        }
    
    def _generate_summary_tweet(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary insights tweet."""
        self.tweet_counter += 1
        
        insights = analytics["insights"]["summary_insights"]
        
        content = "📊 Key Highlights:\n\n"
        for i, insight in enumerate(insights[:4], 1):  # Limit to 4 insights
            content += f"{i}. {insight}\n"
        
        # Add quality metrics if available
        quality = analytics["insights"]["quality_metrics"]
        if quality["total_quality"] > 0:
            content += f"\n🌟 {quality['total_quality']} high-quality papers "
            if quality["spotlights"] > 0 and quality["orals"] > 0:
                content += f"({quality['spotlights']} spotlights, {quality['orals']} orals)"
            elif quality["spotlights"] > 0:
                content += f"({quality['spotlights']} spotlights)"
            elif quality["orals"] > 0:
                content += f"({quality['orals']} orals)"
        
        return {
            "id": self.tweet_counter,
            "type": "summary",
            "content": content,
            "mentions": [],
            "hashtags": ["#IndiaML"],
            "metadata": {
                "character_count": len(content),
                "created_at": datetime.now().isoformat(),
                "insights_count": len(insights)
            }
        }
    
    def _generate_paper_tweets(self, papers: List[Dict[str, Any]], author_lookup: Dict[str, Any], 
                             analytics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tweets for individual papers."""
        paper_tweets = []
        
        # Sort papers by quality (spotlights/orals first)
        sorted_papers = self._sort_papers_by_quality(papers, analytics)
        
        for paper in sorted_papers:
            self.tweet_counter += 1
            
            # Generate paper tweet
            paper_tweet = self._generate_single_paper_tweet(paper, author_lookup, analytics)
            paper_tweets.append(paper_tweet)
        
        return paper_tweets
    
    def _generate_single_paper_tweet(self, paper: Dict[str, Any], author_lookup: Dict[str, Any], 
                                   analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tweet for a single paper."""
        title = paper["title"]
        authors = paper.get("authors", [])
        
        # Determine paper quality
        paper_id = paper["id"]
        is_spotlight = self._is_spotlight_paper(paper_id, analytics)
        is_oral = self._is_oral_paper(paper_id, analytics)
        
        # Start with title
        content = f"📄 {title}\n\n"
        
        # Add quality indicators
        quality_indicators = []
        if is_spotlight:
            quality_indicators.append("🌟 Spotlight")
        if is_oral:
            quality_indicators.append("🎤 Oral")
        
        if quality_indicators:
            content += f"{''.join(quality_indicators)} "
        
        # Add authors with mentions
        mentions = []
        author_texts = []
        
        for author in authors[:5]:  # Limit to first 5 authors
            author_id = str(author.get("author_id", ""))
            author_name = author.get("full_name", "Unknown")
            
            # Get enriched data
            enriched = author_lookup.get(author_id, {})
            twitter_handle = enriched.get("twitter_handle")
            
            if twitter_handle:
                author_texts.append(twitter_handle)
                mentions.append(twitter_handle)
            else:
                author_texts.append(author_name)
        
        # Add "and X more" if there are more authors
        if len(authors) > 5:
            author_texts.append(f"and {len(authors) - 5} more")
        
        content += f"👥 Authors: {', '.join(author_texts)}\n"
        
        # Add institution info for first author
        if authors:
            first_author = authors[0]
            affiliation = first_author.get("affiliation_name", "")
            if affiliation:
                content += f"🏛️ {affiliation}\n"
        
        # Add paper type
        paper_type = "Research Paper"
        if is_spotlight:
            paper_type = "Spotlight Paper"
        elif is_oral:
            paper_type = "Oral Presentation"
        
        content += f"🎯 {paper_type}"
        
        # Add relevant hashtags
        hashtags = ["#ICML2025"]
        
        # Add domain-specific hashtags based on title
        domain_hashtags = self._extract_domain_hashtags(title)
        hashtags.extend(domain_hashtags[:2])  # Limit to 2 domain hashtags
        
        # Add hashtags if they fit
        hashtags_text = " ".join(hashtags)
        if len(content + "\n\n" + hashtags_text) <= self.max_tweet_length:
            content += f"\n\n{hashtags_text}"
        
        return {
            "id": self.tweet_counter,
            "type": "paper",
            "paper_id": paper_id,
            "content": content,
            "mentions": mentions,
            "hashtags": hashtags,
            "authors": self._format_authors_metadata(authors, author_lookup),
            "metadata": {
                "character_count": len(content),
                "created_at": datetime.now().isoformat(),
                "is_spotlight": is_spotlight,
                "is_oral": is_oral,
                "author_count": len(authors),
                "mentions_count": len(mentions)
            }
        }
    
    def _generate_closing_tweet(self, analytics: Dict[str, Any], paper_count: int) -> Dict[str, Any]:
        """Generate closing tweet for the thread."""
        self.tweet_counter += 1
        
        conference_name = analytics["conference"]["name"]
        year = analytics["conference"]["year"]
        
        content = f"🎉 That's a wrap on India's contributions to {conference_name} {year}!\n\n"
        content += f"📊 {paper_count} papers showcasing the growing strength of Indian ML research.\n\n"
        content += "🚀 Exciting to see the innovation coming from Indian institutions and researchers!\n\n"
        content += "Follow @IndiaML for more updates on Indian ML research! 🇮🇳"
        
        hashtags = ["#IndiaML", "#ICML2025", "#Research", "#MachineLearning"]
        
        return {
            "id": self.tweet_counter,
            "type": "closing",
            "content": content,
            "mentions": ["@IndiaML"],
            "hashtags": hashtags,
            "metadata": {
                "character_count": len(content),
                "created_at": datetime.now().isoformat(),
                "paper_count": paper_count
            }
        }
    
    def _sort_papers_by_quality(self, papers: List[Dict[str, Any]], analytics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sort papers by quality (spotlights/orals first)."""
        def quality_score(paper):
            paper_id = paper["id"]
            score = 0
            if self._is_spotlight_paper(paper_id, analytics):
                score += 2
            if self._is_oral_paper(paper_id, analytics):
                score += 1
            return score
        
        return sorted(papers, key=quality_score, reverse=True)
    
    def _is_spotlight_paper(self, paper_id: str, analytics: Dict[str, Any]) -> bool:
        """Check if paper is a spotlight with Indian first author."""
        # Only count spotlights where first author is Indian
        focus_papers = analytics["raw_analytics"].get("focusCountry", {}).get("first_focus_country_author", {}).get("papers", [])
        for paper in focus_papers:
            if paper.get("id") == paper_id:
                return paper.get("isSpotlight", False)
        return False
    
    def _is_oral_paper(self, paper_id: str, analytics: Dict[str, Any]) -> bool:
        """Check if paper is an oral presentation with Indian first author."""
        # Only count orals where first author is Indian
        focus_papers = analytics["raw_analytics"].get("focusCountry", {}).get("first_focus_country_author", {}).get("papers", [])
        for paper in focus_papers:
            if paper.get("id") == paper_id:
                return paper.get("isOral", False)
        return False
    
    def _extract_domain_hashtags(self, title: str) -> List[str]:
        """Extract domain-specific hashtags from paper title."""
        hashtags = []
        title_lower = title.lower()
        
        # Common ML domains
        domain_map = {
            "transformer": "#Transformers",
            "attention": "#Attention",
            "neural": "#NeuralNetworks",
            "deep": "#DeepLearning",
            "reinforcement": "#ReinforcementLearning",
            "computer vision": "#ComputerVision",
            "nlp": "#NLP",
            "language": "#NLP",
            "graph": "#GraphML",
            "optimization": "#Optimization",
            "federated": "#FederatedLearning",
            "diffusion": "#DiffusionModels",
            "generative": "#GenerativeAI",
            "llm": "#LLM",
            "multimodal": "#MultiModal",
            "robotics": "#Robotics",
            "quantum": "#QuantumML"
        }
        
        for keyword, hashtag in domain_map.items():
            if keyword in title_lower:
                hashtags.append(hashtag)
        
        return hashtags
    
    def _format_authors_metadata(self, authors: List[Dict[str, Any]], author_lookup: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format author metadata for tweet."""
        formatted_authors = []
        
        for author in authors:
            author_id = str(author.get("author_id", ""))
            enriched = author_lookup.get(author_id, {})
            
            author_data = {
                "name": author.get("full_name", "Unknown"),
                "affiliation": author.get("affiliation_name", ""),
                "affiliation_country": author.get("affiliation_country", ""),
                "position": author.get("position", 0),
                "twitter_handle": enriched.get("twitter_handle"),
                "twitter_url": enriched.get("twitter_url"),
                "google_scholar": enriched.get("google_scholar_verified"),
                "linkedin": enriched.get("linkedin_verified"),
                "openreview_id": author.get("openreview_id")
            }
            
            formatted_authors.append(author_data)
        
        return formatted_authors
    
    def _calculate_processing_time(self) -> str:
        """Calculate processing time from state."""
        state = self.state_manager.load_state()
        started_at = datetime.fromisoformat(state["started_at"])
        now = datetime.now()
        duration = now - started_at
        
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
