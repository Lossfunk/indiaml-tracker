"""
Enhanced Main Pipeline for Tweet Generation

Orchestrates the complete enhanced tweet generation pipeline with:
- Enhanced JSON extraction with schema detection
- SQLite link hydration
- Enhanced author enrichment with Twitter scraping
- Twitter handle validation
- Tweet generation with validated handles
- Card generation and integration
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the project root to the path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from eda.tweetgen.pipeline.state_manager import StateManager
from eda.tweetgen.pipeline.enhanced_json_extractor import EnhancedJSONExtractor
from eda.tweetgen.pipeline.sqlite_link_hydrator import SQLiteLinkHydrator
from eda.tweetgen.pipeline.author_enricher import AuthorEnricher
from eda.tweetgen.pipeline.twitter_validator import TwitterValidator
from eda.tweetgen.pipeline.analytics_processor import AnalyticsProcessor
from eda.tweetgen.pipeline.tweet_generator import TweetGenerator
from eda.tweetgen.pipeline.card_integrator import CardIntegrator
from eda.tweetgen.pipeline.markdown_generator import MarkdownGenerator
from eda.tweetgen.pipeline.config import PipelineConfig


class TweetGenerationPipeline:
    """Main pipeline orchestrator for tweet generation."""
    
    def __init__(self, conference: str, config: Optional[PipelineConfig] = None, **kwargs):
        self.conference = conference
        
        # Use provided config or create new one
        if config is None:
            self.config = PipelineConfig(conference, **kwargs)
        else:
            self.config = config
        
        # Initialize state manager with config
        self.state_manager = StateManager(conference, str(self.config.output_dir))
        
        # Initialize enhanced pipeline components with config
        self.json_extractor = EnhancedJSONExtractor(self.state_manager, self.config)
        self.sqlite_hydrator = SQLiteLinkHydrator(self.state_manager, self.config)
        self.author_enricher = AuthorEnricher(self.state_manager, self.config)
        self.twitter_validator = TwitterValidator(self.state_manager, self.config)
        self.analytics_processor = AnalyticsProcessor(self.state_manager, self.config)
        self.tweet_generator = TweetGenerator(self.state_manager, self.config)
        self.card_integrator = CardIntegrator(self.state_manager, self.config)
        self.markdown_generator = MarkdownGenerator(self.state_manager, self.config)
    
    async def run(self, force_restart: bool = False, resume_from: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete pipeline."""
        print(f"🚀 Starting Tweet Generation Pipeline for {self.conference}")
        print("=" * 60)
        
        # Initialize or load state
        state = self.state_manager.initialize_state(force_restart)
        
        if resume_from:
            if not self.state_manager.can_resume_from(resume_from):
                raise ValueError(f"Cannot resume from step '{resume_from}'. Previous steps not completed.")
            print(f"📍 Resuming from step: {resume_from}")
        
        try:
            # Get configuration
            config = self._get_conference_config()
            
            # Execute pipeline steps
            results = {}
            
            # Step 1: Initialize
            if not self.state_manager.is_step_completed("initialize"):
                print("\n🔧 Step 1: Initialize")
                self._validate_inputs(config)
                self.state_manager.mark_step_complete("initialize")
                print("  ✅ Initialization complete")
            
            # Step 2: Data Extraction
            if not self.state_manager.is_step_completed("data_extraction"):
                print("\n📊 Step 2: Data Extraction")
                conference_info = self.json_extractor.get_conference_info(self.conference)
                results["conference_info"] = conference_info
                self.state_manager.mark_step_complete("data_extraction", {"conference_info": conference_info})
                print("  ✅ Data extraction complete")
            else:
                state = self.state_manager.load_state()
                results["conference_info"] = state.get("step_metadata", {}).get("data_extraction", {}).get("conference_info", {})
            
            # Step 3: JSON Processing
            if not self.state_manager.is_step_completed("json_processing"):
                print("\n📄 Step 3: JSON Processing")
                data = self.json_extractor.extract_data(self.conference)
                results["papers"] = data["papers"]
                results["authors"] = data["authors"]
                
                # Calculate statistics
                stats = self.json_extractor.get_paper_statistics(data["papers"])
                print(f"  📊 Statistics: {stats['total_papers']} papers, {stats['total_indian_authors']} Indian authors")
                
                self.state_manager.mark_step_complete("json_processing", {"statistics": stats})
                print("  ✅ JSON processing complete")
            else:
                results["papers"] = self.state_manager.load_checkpoint("raw_papers.json")
                results["authors"] = self.state_manager.load_checkpoint("raw_authors.json")
            
            # Step 4: SQLite Link Hydration
            if not self.state_manager.is_step_completed("sqlite_hydration"):
                print("\n🔗 Step 4: SQLite Link Hydration")
                hydrated_authors = self.sqlite_hydrator.hydrate_authors(results["authors"])
                results["hydrated_authors"] = hydrated_authors
                self.state_manager.mark_step_complete("sqlite_hydration")
                print("  ✅ SQLite hydration complete")
            else:
                results["hydrated_authors"] = self.state_manager.load_checkpoint("hydrated_authors.json")
            
            # Step 5: Author Enrichment (Enhanced with Twitter Scraping)
            if not self.state_manager.is_step_completed("author_enrichment"):
                print("\n🔍 Step 5: Enhanced Author Enrichment")
                enriched_authors = await self.author_enricher.enrich_authors(results["hydrated_authors"])
                results["enriched_authors"] = enriched_authors
                self.state_manager.mark_step_complete("author_enrichment")
                print("  ✅ Author enrichment complete")
            else:
                results["enriched_authors"] = self.state_manager.load_checkpoint("enriched_authors.json")
            
            # Step 6: Twitter Handle Validation
            if not self.state_manager.is_step_completed("twitter_validation"):
                print("\n🐦 Step 6: Twitter Handle Validation")
                validated_authors = self.twitter_validator.validate_authors(results["enriched_authors"])
                results["validated_authors"] = validated_authors
                self.state_manager.mark_step_complete("twitter_validation")
                print("  ✅ Twitter validation complete")
            else:
                results["validated_authors"] = self.state_manager.load_checkpoint("validated_authors.json")
            
            # Step 7: Analytics Processing
            if not self.state_manager.is_step_completed("analytics_processing"):
                print("\n📈 Step 7: Analytics Processing")
                analytics = self.analytics_processor.process_analytics(
                    config["analytics_file"], 
                    results["conference_info"]
                )
                results["analytics"] = analytics
                self.state_manager.mark_step_complete("analytics_processing")
                print("  ✅ Analytics processing complete")
            else:
                results["analytics"] = self.state_manager.load_checkpoint("processed_analytics.json")
            
            # Step 8: Enhanced Tweet Generation
            if not self.state_manager.is_step_completed("tweet_generation"):
                print("\n🐦 Step 8: Enhanced Tweet Generation")
                tweet_thread = self.tweet_generator.generate_tweet_thread(
                    results["papers"],
                    results["validated_authors"],
                    results["analytics"]
                )
                results["tweet_thread"] = tweet_thread
                self.state_manager.mark_step_complete("tweet_generation")
                print("  ✅ Tweet generation complete")
            else:
                results["tweet_thread"] = self.state_manager.load_checkpoint("tweet_thread.json")
            
            # Step 9: Card Generation and Integration
            if not self.state_manager.is_step_completed("card_generation"):
                print("\n🎨 Step 9: Card Generation and Integration")
                card_results = self.card_integrator.generate_cards_for_tweets(
                    results["papers"],
                    results["tweet_thread"]
                )
                results["card_results"] = card_results
                results["enhanced_tweet_thread"] = card_results["enhanced_tweet_thread"]
                self.state_manager.mark_step_complete("card_generation")
                print("  ✅ Card generation complete")
            else:
                results["card_results"] = self.state_manager.load_checkpoint("generated_cards.json")
                results["enhanced_tweet_thread"] = results["card_results"]["enhanced_tweet_thread"]
            
            # Step 10: Markdown Generation
            if not self.state_manager.is_step_completed("markdown_generation"):
                print("\n📝 Step 10: Markdown Generation")
                # Use enhanced tweet thread with cards
                final_thread = results.get("enhanced_tweet_thread", results["tweet_thread"])
                markdown_content = self.markdown_generator.generate_markdown(final_thread)
                summary_content = self.markdown_generator.generate_summary_markdown(final_thread)
                results["markdown"] = markdown_content
                results["summary"] = summary_content
                self.state_manager.mark_step_complete("markdown_generation")
                print("  ✅ Markdown generation complete")
            else:
                with open(self.state_manager.get_checkpoint_file("tweet_thread.md"), 'r', encoding='utf-8') as f:
                    results["markdown"] = f.read()
                with open(self.state_manager.conference_dir / "summary.md", 'r', encoding='utf-8') as f:
                    results["summary"] = f.read()
            
            # Step 11: Finalize
            if not self.state_manager.is_step_completed("finalize"):
                print("\n🎉 Step 11: Finalize")
                self._finalize_outputs(results)
                self.state_manager.mark_step_complete("finalize")
                print("  ✅ Enhanced Pipeline complete!")
            
            # Print final summary
            self._print_final_summary(results)
            
            return results
            
        except Exception as e:
            current_step = self.state_manager.get_next_step()
            if current_step:
                self.state_manager.mark_step_failed(current_step, str(e))
            print(f"\n❌ Pipeline failed: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        return self.state_manager.get_status()
    
    def _get_conference_config(self) -> Dict[str, str]:
        """Get configuration for the conference."""
        return self.config.get_conference_config()
    
    def _validate_inputs(self, config: Dict[str, str]) -> None:
        """Validate that required input files exist."""
        try:
            # Check JSON file exists
            json_path = self.config.get_json_path()
            if not json_path.exists():
                raise FileNotFoundError(f"JSON file not found: {json_path}")
            print(f"  ✅ JSON file: {json_path}")
            
            # Check analytics file exists
            analytics_path = self.config.get_analytics_path()
            if not analytics_path.exists():
                raise FileNotFoundError(f"Analytics file not found: {analytics_path}")
            print(f"  ✅ Analytics file: {analytics_path}")
            
            # Print configuration summary
            print(f"  🔧 Configuration:")
            print(f"    • Analytics directory: {self.config.analytics_dir}")
            print(f"    • Output directory: {self.config.output_dir}")
            print(f"    • Max concurrent requests: {self.config.max_concurrent_requests}")
            print(f"    • API keys available: {self.config.has_api_keys()}")
            
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Configuration validation failed: {e}")
    
    def _finalize_outputs(self, results: Dict[str, Any]) -> None:
        """Finalize and organize output files."""
        output_dir = self.state_manager.conference_dir
        
        # Copy final JSON to main output directory
        final_json = output_dir / "tweet_thread.json"
        if not final_json.exists():
            with open(final_json, 'w', encoding='utf-8') as f:
                json.dump(results["tweet_thread"], f, indent=2, ensure_ascii=False)
        
        # Create a final summary JSON
        summary_json = {
            "conference": self.conference,
            "pipeline_status": "completed",
            "generated_at": results["tweet_thread"]["generated_at"],
            "files": {
                "tweet_thread_json": str(final_json),
                "tweet_thread_md": str(output_dir / "tweet_thread.md"),
                "summary_md": str(output_dir / "summary.md")
            },
            "statistics": results["tweet_thread"]["metadata"],
            "analytics_summary": results["tweet_thread"]["analytics_summary"]
        }
        
        with open(output_dir / "pipeline_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary_json, f, indent=2, ensure_ascii=False)
        
        print(f"  📁 Output directory: {output_dir}")
        print(f"  📄 Tweet thread JSON: {final_json}")
        print(f"  📝 Tweet thread MD: {output_dir / 'tweet_thread.md'}")
        print(f"  📋 Summary MD: {output_dir / 'summary.md'}")
    
    def _print_final_summary(self, results: Dict[str, Any]) -> None:
        """Print final pipeline summary."""
        tweet_thread = results["tweet_thread"]
        metadata = tweet_thread["metadata"]
        analytics = tweet_thread["analytics_summary"]
        
        print("\n" + "=" * 60)
        print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Conference: {tweet_thread['conference']} {tweet_thread['year']}")
        print(f"Processing time: {metadata['processing_time']}")
        print()
        print("📊 Results:")
        print(f"  • {metadata['total_tweets']} tweets generated")
        print(f"  • {metadata['total_papers']} papers covered")
        print(f"  • {metadata['total_authors']} authors processed")
        print(f"  • {analytics['india_papers']} Indian papers")
        print(f"  • Global rank: #{analytics['global_rank']}")
        print(f"  • APAC rank: #{analytics['apac_rank']}")
        print(f"  • Quality papers: {analytics['quality_papers']}")
        print()
        print(f"📁 Output: {self.state_manager.conference_dir}")
        print("=" * 60)


async def main():
    """Main entry point for running the pipeline."""
    if len(sys.argv) < 2:
        print("Usage: python pipeline/enhanced_pipeline.py <conference> [--force-restart] [--resume-from <step>]")
        print("Example: python pipeline/enhanced_pipeline.py icml-2025")
        sys.exit(1)
    
    conference = sys.argv[1]
    force_restart = "--force-restart" in sys.argv
    resume_from = None
    
    if "--resume-from" in sys.argv:
        try:
            resume_index = sys.argv.index("--resume-from")
            resume_from = sys.argv[resume_index + 1]
        except (IndexError, ValueError):
            print("Error: --resume-from requires a step name")
            sys.exit(1)
    
    pipeline = TweetGenerationPipeline(conference)
    
    try:
        results = await pipeline.run(force_restart=force_restart, resume_from=resume_from)
        print("\n✅ Pipeline completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        status = pipeline.get_status()
        print(f"Status: {status}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
