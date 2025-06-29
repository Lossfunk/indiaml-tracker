#!/usr/bin/env python3
"""
CLI Script for Tweet Generation Pipeline

Easy-to-use command line interface for running the tweet generation pipeline.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from pipeline.main_pipeline import TweetGenerationPipeline
from pipeline.config import PipelineConfig


def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate tweet threads from conference data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate tweets for ICML 2025
  python run_pipeline.py icml-2025

  # Force restart the pipeline
  python run_pipeline.py icml-2025 --force-restart

  # Resume from a specific step
  python run_pipeline.py icml-2025 --resume-from author_enrichment

  # Check status of existing pipeline
  python run_pipeline.py icml-2025 --status

  # Custom data directories
  python run_pipeline.py icml-2025 --data-dir /path/to/data --analytics-dir /path/to/analytics

  # Performance tuning
  python run_pipeline.py icml-2025 --max-concurrent 5 --request-timeout 60

Available conferences:
  - icml-2025, icml-2024
  - iclr-2025, iclr-2024
  - neurips-2024
  - Or any conference with auto-detection
        """
    )
    
    # Required arguments
    parser.add_argument(
        "conference",
        help="Conference to process (e.g., icml-2025, iclr-2025, neurips-2024)"
    )
    
    # Pipeline control
    parser.add_argument(
        "--force-restart",
        action="store_true",
        help="Force restart the pipeline from the beginning"
    )
    
    parser.add_argument(
        "--resume-from",
        metavar="STEP",
        help="Resume pipeline from a specific step"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current pipeline status and exit"
    )
    
    parser.add_argument(
        "--list-steps",
        action="store_true",
        help="List all pipeline steps and exit"
    )
    
    # Directory configuration
    parser.add_argument(
        "--data-dir",
        help="Directory containing SQLite database files (default: data/)"
    )
    
    parser.add_argument(
        "--analytics-dir",
        help="Directory containing analytics JSON files (default: ui/indiaml-tracker/public/tracker/)"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Output directory for generated files (default: eda/tweetgen/outputs)"
    )
    
    # Performance settings
    parser.add_argument(
        "--max-concurrent",
        type=int,
        help="Maximum concurrent requests for author enrichment (default: 3)"
    )
    
    parser.add_argument(
        "--request-timeout",
        type=int,
        help="Request timeout in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--rate-limit-delay",
        type=float,
        help="Delay between request batches in seconds (default: 2.0)"
    )
    
    # Tweet generation settings
    parser.add_argument(
        "--max-tweet-length",
        type=int,
        help="Maximum tweet length (default: 280)"
    )
    
    parser.add_argument(
        "--max-authors-per-tweet",
        type=int,
        help="Maximum authors to mention per tweet (default: 5)"
    )
    
    # Configuration management
    parser.add_argument(
        "--config-file",
        help="Path to conference configuration JSON file"
    )
    
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="Save current configuration to file"
    )
    
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show current configuration and exit"
    )
    
    return parser


def print_pipeline_steps():
    """Print all available pipeline steps."""
    steps = [
        "initialize",
        "data_extraction", 
        "sqlite_processing",
        "author_enrichment",
        "analytics_processing",
        "tweet_generation",
        "markdown_generation",
        "finalize"
    ]
    
    print("Available pipeline steps:")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")


async def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle special commands
    if args.list_steps:
        print_pipeline_steps()
        return
    
    # Create configuration from CLI arguments
    try:
        config = PipelineConfig.from_cli_args(args)
        
        # Handle configuration commands
        if args.show_config:
            print_config(config)
            return
        
        if args.save_config:
            save_config_to_file(config, args.config_file)
            return
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return 1
    
    # Create pipeline with configuration
    try:
        pipeline = TweetGenerationPipeline(args.conference, config=config)
    except Exception as e:
        print(f"❌ Pipeline creation error: {e}")
        return 1
    
    # Handle status command
    if args.status:
        status = pipeline.get_status()
        print_status(status)
        return
    
    # Validate arguments
    if args.resume_from and args.force_restart:
        print("❌ Error: Cannot use --resume-from with --force-restart")
        return 1
    
    # Run pipeline
    try:
        print(f"🚀 Starting pipeline for {args.conference}")
        if args.force_restart:
            print("🔄 Force restarting from beginning...")
        elif args.resume_from:
            print(f"📍 Resuming from step: {args.resume_from}")
        
        results = await pipeline.run(
            force_restart=args.force_restart,
            resume_from=args.resume_from
        )
        
        print("\n✅ Pipeline completed successfully!")
        print(f"📁 Output directory: {pipeline.state_manager.conference_dir}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        status = pipeline.get_status()
        print(f"Current status: {status.get('status', 'unknown')}")
        return 1
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        status = pipeline.get_status()
        print_status(status)
        return 1


def print_config(config: PipelineConfig):
    """Print current configuration."""
    print("\n🔧 Current Configuration:")
    print("=" * 40)
    
    config_dict = config.to_dict()
    for key, value in config_dict.items():
        if key == "api_config" and isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                if sub_key == "api_key" and sub_value:
                    # Mask API key for security
                    masked_key = sub_value[:8] + "..." + sub_value[-4:] if len(sub_value) > 12 else "***"
                    print(f"  {sub_key}: {masked_key}")
                else:
                    print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")


def save_config_to_file(config: PipelineConfig, config_file: str = None):
    """Save configuration to file."""
    from pipeline.config import save_conference_config_file
    
    if config_file is None:
        config_file = "eda/tweetgen/conference_config.json"
    
    # Get current mappings and add this conference
    try:
        from pipeline.config import load_conference_config_file
        existing_config = load_conference_config_file(config_file)
    except:
        existing_config = {}
    
    # Add current conference configuration
    conference_config = config.get_conference_config()
    existing_config[config.conference] = conference_config
    
    save_conference_config_file(existing_config, config_file)
    print(f"✅ Configuration saved to {config_file}")


def print_status(status):
    """Print pipeline status in a formatted way."""
    print("\n📊 Pipeline Status:")
    print("=" * 40)
    
    if status.get("status") == "not_started":
        print("Status: Not started")
        return
    
    print(f"Conference: {status.get('conference', 'Unknown')}")
    print(f"Pipeline ID: {status.get('pipeline_id', 'Unknown')}")
    print(f"Status: {status.get('status', 'Unknown')}")
    print(f"Progress: {status.get('progress_percentage', 0):.1f}%")
    print(f"Current step: {status.get('current_step', 'Unknown')}")
    
    if status.get('started_at'):
        print(f"Started: {status['started_at']}")
    
    if status.get('completed_at'):
        print(f"Completed: {status['completed_at']}")
    
    completed = status.get('completed_steps', [])
    failed = status.get('failed_steps', [])
    
    if completed:
        print(f"\n✅ Completed steps ({len(completed)}):")
        for step in completed:
            print(f"  • {step}")
    
    if failed:
        print(f"\n❌ Failed steps ({len(failed)}):")
        for step in failed:
            print(f"  • {step}")
    
    progress = status.get('progress', {})
    if progress:
        print(f"\n📈 Progress:")
        for key, value in progress.items():
            print(f"  • {key}: {value}")
    
    errors = status.get('errors', [])
    if errors:
        print(f"\n🚨 Recent errors:")
        for error in errors[-3:]:  # Show last 3 errors
            print(f"  • {error.get('step', 'Unknown')}: {error.get('error', 'Unknown error')}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
