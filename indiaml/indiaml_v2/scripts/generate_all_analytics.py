#!/usr/bin/env python3
"""
Batch script to generate analytics for all available years across all venues.
Focus country: India (IN)
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from indiaml_v2.analytics.analytics_pipeline import AnalyticsPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_analytics_for_venue(db_path, venue_name, years, output_base_dir, focus_country="IN"):
    """Generate analytics for all years of a specific venue."""
    if "icml" in db_path:
        venue_output_dir = Path(output_base_dir) / f"{venue_name.lower()}-v2"
    elif "neurips" in db_path:
        venue_output_dir = Path(output_base_dir) / f"{venue_name.lower()}-v1.4"
    else:
        venue_output_dir = Path(output_base_dir) / f"{venue_name.lower()}-v1"
    venue_output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for year in years:
        try:
            output_file = venue_output_dir / f"{venue_name.lower()}-{year}-analytics.json"
            
            logger.info(f"Generating {venue_name} {year} analytics...")
            start_time = time.time()
            
            with AnalyticsPipeline(db_path) as pipeline:
                analytics = pipeline.generate_analytics(
                    conference_name=venue_name,
                    year=year,
                    focus_country_code=focus_country,
                    output_path=str(output_file)
                )
            
            end_time = time.time()
            
            # Extract key metrics
            focus_summary = analytics.get('focusCountrySummary', {})
            paper_count = focus_summary.get('paper_count', 0)
            rank = focus_summary.get('rank', 'N/A')
            
            result = {
                'venue': venue_name,
                'year': year,
                'output_file': str(output_file),
                'paper_count': paper_count,
                'rank': rank,
                'duration': round(end_time - start_time, 2),
                'success': True
            }
            
            logger.info(f"✓ {venue_name} {year}: {paper_count} papers, rank {rank} ({result['duration']}s)")
            results.append(result)
            
        except Exception as e:
            logger.error(f"✗ Failed to generate {venue_name} {year}: {e}")
            results.append({
                'venue': venue_name,
                'year': year,
                'success': False,
                'error': str(e)
            })
    
    return results

def main():
    """Main function to generate all analytics."""
    # Configuration
    focus_country = "IN"
    base_dir = Path(__file__).parent.parent.parent.parent
    data_dir = base_dir / "data_v2"
    output_dir = base_dir / "ui" / "indiaml-tracker" / "public" / "tracker_v2"
    
    # Database configurations
    venues = [
        {
            'name': 'ICML',
            'db_path': str(data_dir / "icml-v2.db"),
            'years': list(range(2013, 2026))  # 2013-2025
        },
        {
            'name': 'ICLR',
            'db_path': str(data_dir / "iclr-v1.db"),
            'years': [2013, 2014] + list(range(2017, 2026))  # 2013, 2014, 2017-2025
        },
        {
            'name': 'NeurIPS',
            'db_path': str(data_dir / "neurips_v1.4.db"),
            'years': list(range(1987, 2025))  # All available years: 1987-2024
        }
    ]
    
    logger.info(f"Starting batch analytics generation for focus country: {focus_country}")
    logger.info(f"Output directory: {output_dir}")
    
    all_results = []
    total_start_time = time.time()
    
    for venue_config in venues:
        venue_name = venue_config['name']
        db_path = venue_config['db_path']
        years = venue_config['years']
        
        if not Path(db_path).exists():
            logger.warning(f"Database not found: {db_path}")
            continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {venue_name} ({len(years)} years)")
        logger.info(f"Database: {db_path}")
        logger.info(f"Years: {min(years)}-{max(years)}")
        logger.info(f"{'='*60}")
        
        venue_results = generate_analytics_for_venue(
            db_path, venue_name, years, str(output_dir), focus_country
        )
        all_results.extend(venue_results)
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Summary
    successful = [r for r in all_results if r.get('success', False)]
    failed = [r for r in all_results if not r.get('success', False)]
    
    logger.info(f"\n{'='*60}")
    logger.info("BATCH ANALYTICS GENERATION COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Total time: {total_duration:.2f} seconds")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n✅ Successfully generated analytics:")
        for result in successful:
            logger.info(f"  {result['venue']} {result['year']}: {result['paper_count']} papers, rank {result['rank']}")
    
    if failed:
        logger.info(f"\n❌ Failed generations:")
        for result in failed:
            logger.info(f"  {result['venue']} {result['year']}: {result.get('error', 'Unknown error')}")
    
    # Generate updated index.json
    generate_index_file(successful, output_dir)
    
    return len(failed) == 0

def generate_index_file(successful_results, output_dir):
    """Generate updated index.json file with all successful analytics."""
    import json
    
    index_entries = []
    
    # Group by venue and sort
    venues = {}
    for result in successful_results:
        venue = result['venue']
        if venue not in venues:
            venues[venue] = []
        venues[venue].append(result)
    
    # Sort each venue by year (descending)
    for venue in venues:
        venues[venue].sort(key=lambda x: x['year'], reverse=True)
    
    # Create index entries
    for venue_name in ['ICML', 'ICLR', 'NeurIPS']:
        if venue_name not in venues:
            continue
            
        for result in venues[venue_name]:
            year = result['year']
            venue_lower = venue_name.lower()
            
            # Determine version suffix and analytics path
            if venue_name == 'ICML':
                version_suffix = "v2"
                db_file = "icml-v2.db"
                analytics_folder = f"{venue_lower}-v2"
            elif venue_name == 'ICLR':
                version_suffix = "v1"
                db_file = "iclr-v1.db"
                analytics_folder = f"{venue_lower}-v1"
            else:  # NeurIPS
                version_suffix = "v1"
                db_file = "neurips_v1.4.db"
                analytics_folder = f"{venue_lower}-v1.4"
            
            entry = {
                "label": f"{venue_name} {year} {version_suffix}",
                "file": f"{venue_lower}-{year}-{version_suffix}.json",
                "analytics": f"{analytics_folder}/{venue_lower}-{year}-analytics.json",
                "venue": venue_lower,
                "year": str(year),
                "sqlite_file": db_file
            }
            index_entries.append(entry)
    
    # Save index file
    index_file = Path(output_dir) / "index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_entries, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Updated index file: {index_file}")
    logger.info(f"  Total entries: {len(index_entries)}")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
