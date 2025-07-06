#!/usr/bin/env python3
"""
Example usage and utilities for the Academic Paper Data Transformation Pipeline

This script demonstrates how to use the pipeline with various configurations
and includes utility functions for common tasks.
"""

import argparse
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd

from indiaml_v2.pipeline.paper_pipeline import (
    PaperDataPipeline, PipelineConfig, StatusNormalizer, 
    CountryCodeMapper, SortingCalculator
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PipelineRunner:
    """Utility class for running the pipeline with different configurations"""
    
    PRESET_CONFIGS = {
        'conservative': PipelineConfig(
            first_author_weight=2.0,
            last_author_weight=1.5,
            middle_author_weight=1.0,
            status_weights={
                'oral': 8.0,
                'spotlight': 6.0,
                'poster': 4.0,
                'unknown': 1.0
            }
        ),
        'aggressive': PipelineConfig(
            first_author_weight=5.0,
            last_author_weight=3.0,
            middle_author_weight=0.5,
            status_weights={
                'oral': 20.0,
                'spotlight': 12.0,
                'poster': 5.0,
                'unknown': 1.0
            }
        ),
        'balanced': PipelineConfig(
            first_author_weight=3.0,
            last_author_weight=2.0,
            middle_author_weight=1.0,
            status_weights={
                'oral': 10.0,
                'spotlight': 7.5,
                'poster': 5.0,
                'unknown': 1.0
            }
        ),
        'egalitarian': PipelineConfig(
            first_author_weight=1.5,
            last_author_weight=1.5,
            middle_author_weight=1.0,
            status_weights={
                'oral': 3.0,
                'spotlight': 2.5,
                'poster': 2.0,
                'unknown': 1.0
            }
        )
    }
    
    @classmethod
    def run_with_preset(cls, db_path: str, focus_country: str, output_dir: str, 
                       preset: str = 'balanced', output_format: str = 'json') -> Dict[str, str]:
        """Run pipeline with a preset configuration"""
        if preset not in cls.PRESET_CONFIGS:
            raise ValueError(f"Unknown preset: {preset}. Available: {list(cls.PRESET_CONFIGS.keys())}")
        
        config = cls.PRESET_CONFIGS[preset]
        config.output_format = output_format
        
        logger.info(f"Running pipeline with {preset} preset for {focus_country}")
        pipeline = PaperDataPipeline(db_path, config)
        
        start_time = time.time()
        result = pipeline.process_and_export(focus_country, output_dir)
        end_time = time.time()
        
        logger.info(f"Pipeline completed in {end_time - start_time:.2f} seconds")
        return result
    
    @classmethod
    def compare_presets(cls, db_path: str, focus_country: str, output_base_dir: str) -> Dict:
        """Compare results across different presets"""
        results = {}
        
        for preset_name in cls.PRESET_CONFIGS.keys():
            logger.info(f"Running {preset_name} preset...")
            
            preset_output_dir = Path(output_base_dir) / f"{preset_name}_preset"
            preset_output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                output_files = cls.run_with_preset(
                    db_path, focus_country, str(preset_output_dir), preset_name
                )
                results[preset_name] = {
                    'success': True,
                    'output_files': output_files,
                    'output_dir': str(preset_output_dir)
                }
            except Exception as e:
                logger.error(f"Failed to run {preset_name} preset: {e}")
                results[preset_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results

class AnalysisUtils:
    """Utility functions for analyzing pipeline results"""
    
    @staticmethod
    def analyze_json_output(json_file_path: str) -> Dict:
        """Analyze a JSON output file and provide statistics"""
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        papers = data['papers']
        
        # Basic statistics
        stats = {
            'total_papers': len(papers),
            'conference': data['conference'],
            'focus_country': data['focus_country']
        }
        
        # Status distribution
        status_dist = {}
        for paper in papers:
            status = paper['normalized_status']
            status_dist[status] = status_dist.get(status, 0) + 1
        stats['status_distribution'] = status_dist
        
        # Author position distribution
        position_dist = {}
        for paper in papers:
            pos = paper['author']['position']
            position_dist[pos] = position_dist.get(pos, 0) + 1
        stats['author_position_distribution'] = position_dist
        
        # Score statistics
        scores = [p['sort_score'] for p in papers if p['sort_score'] > 0]
        if scores:
            stats['score_stats'] = {
                'min': min(scores),
                'max': max(scores),
                'mean': sum(scores) / len(scores),
                'median': sorted(scores)[len(scores) // 2]
            }
        
        # Top papers
        top_papers = sorted(papers, key=lambda x: x['sort_score'], reverse=True)[:5]
        stats['top_papers'] = [
            {
                'title': p['title'],
                'status': p['normalized_status'],
                'author_position': p['author']['position'],
                'score': p['sort_score']
            }
            for p in top_papers
        ]
        
        # Review statistics (if available)
        papers_with_reviews = [p for p in papers if 'reviews' in p]
        if papers_with_reviews:
            ratings = [p['reviews']['rating_mean'] for p in papers_with_reviews if p['reviews']['rating_mean']]
            if ratings:
                stats['review_stats'] = {
                    'papers_with_reviews': len(papers_with_reviews),
                    'avg_rating': sum(ratings) / len(ratings),
                    'min_rating': min(ratings),
                    'max_rating': max(ratings)
                }
        
        return stats
    
    @staticmethod
    def compare_presets_analysis(preset_results: Dict, output_file: str = None) -> Dict:
        """Compare statistics across different presets"""
        comparison = {}
        
        for preset_name, preset_result in preset_results.items():
            if not preset_result['success']:
                continue
                
            preset_stats = {}
            for conf_name, file_path in preset_result['output_files'].items():
                if file_path.endswith('.json'):
                    stats = AnalysisUtils.analyze_json_output(file_path)
                    preset_stats[conf_name] = stats
            
            comparison[preset_name] = preset_stats
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(comparison, f, indent=2)
        
        return comparison
    
    @staticmethod
    def generate_summary_report(analysis_results: Dict, output_file: str):
        """Generate a markdown summary report"""
        with open(output_file, 'w') as f:
            f.write("# Academic Paper Analysis Report\n\n")
            
            for preset_name, preset_data in analysis_results.items():
                f.write(f"## {preset_name.title()} Preset\n\n")
                
                for conf_name, stats in preset_data.items():
                    f.write(f"### {conf_name}\n\n")
                    f.write(f"- **Total Papers**: {stats['total_papers']}\n")
                    f.write(f"- **Focus Country**: {stats['focus_country']}\n\n")
                    
                    # Status distribution
                    f.write("**Status Distribution:**\n")
                    for status, count in stats['status_distribution'].items():
                        f.write(f"- {status.title()}: {count}\n")
                    f.write("\n")
                    
                    # Top papers
                    if 'top_papers' in stats:
                        f.write("**Top 5 Papers:**\n")
                        for i, paper in enumerate(stats['top_papers'], 1):
                            f.write(f"{i}. {paper['title']} (Score: {paper['score']:.2f})\n")
                            f.write(f"   - Status: {paper['status']}, Author Position: {paper['author_position']}\n")
                        f.write("\n")
                    
                    f.write("---\n\n")

class ValidationUtils:
    """Utilities for validating input data and results"""
    
    @staticmethod
    def validate_database(db_path: str) -> Dict[str, bool]:
        """Validate that the database has required tables and data"""
        import sqlite3
        
        required_tables = [
            'papers', 'authors', 'affiliations', 'institutions', 
            'countries', 'conferences', 'tracks', 'paper_authors'
        ]
        
        validation_results = {}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in required_tables:
                validation_results[f"table_{table}_exists"] = table in existing_tables
                
                if table in existing_tables:
                    # Check if table has data
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    validation_results[f"table_{table}_has_data"] = count > 0
            
            conn.close()
            
        except Exception as e:
            validation_results['database_accessible'] = False
            validation_results['error'] = str(e)
        
        return validation_results
    
    @staticmethod
    def suggest_countries(db_path: str, limit: int = 20) -> List[Dict]:
        """Suggest countries based on number of affiliated authors"""
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        
        query = """
        SELECT 
            c.name as country,
            COUNT(DISTINCT a.id) as author_count,
            COUNT(DISTINCT p.id) as paper_count
        FROM countries c
        JOIN institutions i ON c.id = i.country_id
        JOIN affiliations af ON i.id = af.institution_id
        JOIN authors a ON af.author_id = a.id
        JOIN paper_authors pa ON a.id = pa.author_id
        JOIN papers p ON pa.paper_id = p.id
        GROUP BY c.name
        ORDER BY author_count DESC
        LIMIT ?
        """
        
        cursor = conn.execute(query, (limit,))
        suggestions = []
        
        for row in cursor.fetchall():
            suggestions.append({
                'country': row[0],
                'author_count': row[1],
                'paper_count': row[2],
                'country_code': CountryCodeMapper.get_country_code(row[0])
            })
        
        conn.close()
        return suggestions

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Academic Paper Data Transformation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s process data.db "United States" ./output --preset balanced
  %(prog)s compare data.db "China" ./comparison_output
  %(prog)s validate data.db
  %(prog)s suggest-countries data.db --limit 10
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process data for a focus country')
    process_parser.add_argument('database', help='Path to SQLite database')
    process_parser.add_argument('country', help='Focus country name')
    process_parser.add_argument('output_dir', help='Output directory')
    process_parser.add_argument('--preset', choices=list(PipelineRunner.PRESET_CONFIGS.keys()), 
                               default='balanced', help='Configuration preset')
    process_parser.add_argument('--format', choices=['json', 'csv'], default='json', 
                               help='Output format')
    process_parser.add_argument('--analyze', action='store_true', 
                               help='Generate analysis report')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare results across presets')
    compare_parser.add_argument('database', help='Path to SQLite database')
    compare_parser.add_argument('country', help='Focus country name')
    compare_parser.add_argument('output_dir', help='Base output directory')
    compare_parser.add_argument('--report', help='Generate comparison report file')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate database structure')
    validate_parser.add_argument('database', help='Path to SQLite database')
    
    # Suggest countries command
    suggest_parser = subparsers.add_parser('suggest-countries', help='Suggest focus countries')
    suggest_parser.add_argument('database', help='Path to SQLite database')
    suggest_parser.add_argument('--limit', type=int, default=20, help='Number of suggestions')
    
    args = parser.parse_args()
    
    if args.command == 'process':
        try:
            output_files = PipelineRunner.run_with_preset(
                args.database, args.country, args.output_dir, 
                args.preset, args.format
            )
            
            print(f"Processing completed successfully!")
            print(f"Output files:")
            for conf, filepath in output_files.items():
                print(f"  {conf}: {filepath}")
            
            if args.analyze:
                print("\nGenerating analysis...")
                for conf, filepath in output_files.items():
                    if filepath.endswith('.json'):
                        stats = AnalysisUtils.analyze_json_output(filepath)
                        print(f"\n{conf} Statistics:")
                        print(f"  Total papers: {stats['total_papers']}")
                        print(f"  Status distribution: {stats['status_distribution']}")
                        if 'score_stats' in stats:
                            print(f"  Score range: {stats['score_stats']['min']:.2f} - {stats['score_stats']['max']:.2f}")
                        
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            sys.exit(1)
    
    elif args.command == 'compare':
        try:
            results = PipelineRunner.compare_presets(
                args.database, args.country, args.output_dir
            )
            
            print("Comparison completed!")
            for preset, result in results.items():
                if result['success']:
                    print(f"  {preset}: ✓ Success")
                else:
                    print(f"  {preset}: ✗ Failed - {result['error']}")
            
            if args.report:
                analysis = AnalysisUtils.compare_presets_analysis(results)
                AnalysisUtils.generate_summary_report(analysis, args.report)
                print(f"Report generated: {args.report}")
                
        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            sys.exit(1)
    
    elif args.command == 'validate':
        try:
            validation_results = ValidationUtils.validate_database(args.database)
            
            print("Database validation results:")
            all_good = True
            for check, passed in validation_results.items():
                if check == 'error':
                    continue
                status = "✓" if passed else "✗"
                print(f"  {check}: {status}")
                if not passed:
                    all_good = False
            
            if 'error' in validation_results:
                print(f"Error: {validation_results['error']}")
                all_good = False
            
            if all_good:
                print("\nDatabase validation passed!")
            else:
                print("\nDatabase validation failed!")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            sys.exit(1)
    
    elif args.command == 'suggest-countries':
        try:
            suggestions = ValidationUtils.suggest_countries(args.database, args.limit)
            
            print(f"Top {args.limit} countries by author count:")
            print(f"{'Country':<30} {'Code':<6} {'Authors':<8} {'Papers':<8}")
            print("-" * 54)
            
            for suggestion in suggestions:
                print(f"{suggestion['country']:<30} {suggestion['country_code']:<6} "
                      f"{suggestion['author_count']:<8} {suggestion['paper_count']:<8}")
                
        except Exception as e:
            logger.error(f"Suggestion failed: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()