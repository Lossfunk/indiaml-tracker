#!/usr/bin/env python3
"""
SQLite to Analytics JSON Pipeline

This script generates comprehensive analytics JSON files from v2 database schema,
compatible with the existing UI but leveraging the improved normalized data structure.
"""

import argparse
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional

from indiaml_v2.analytics.analytics_pipeline import AnalyticsPipeline
from indiaml_v2.analytics.config import DEFAULT_CONFIG, COUNTRY_CODE_MAP

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnalyticsRunner:
    """Utility class for running analytics generation with different configurations."""
    
    @classmethod
    def generate_single_analytics(cls, db_path: str, conference_name: str, year: int,
                                focus_country_code: str = "IN", track_name: str = None,
                                output_path: str = None) -> Dict[str, any]:
        """Generate analytics for a single conference."""
        logger.info(f"Generating analytics for {conference_name} {year}")
        
        start_time = time.time()
        
        with AnalyticsPipeline(db_path) as pipeline:
            analytics = pipeline.generate_analytics(
                conference_name=conference_name,
                year=year,
                focus_country_code=focus_country_code,
                track_name=track_name,
                output_path=output_path
            )
        
        end_time = time.time()
        logger.info(f"Analytics generation completed in {end_time - start_time:.2f} seconds")
        
        return analytics
    
    @classmethod
    def generate_batch_analytics(cls, db_path: str, conferences: List[Dict],
                               output_dir: str, focus_country_code: str = "IN") -> Dict[str, str]:
        """Generate analytics for multiple conferences."""
        logger.info(f"Generating batch analytics for {len(conferences)} conferences")
        
        start_time = time.time()
        
        with AnalyticsPipeline(db_path) as pipeline:
            output_files = pipeline.generate_batch_analytics(
                conferences=conferences,
                output_dir=output_dir,
                focus_country_code=focus_country_code
            )
        
        end_time = time.time()
        logger.info(f"Batch analytics generation completed in {end_time - start_time:.2f} seconds")
        
        return output_files
    
    @classmethod
    def generate_from_config(cls, config_file: str, output_dir: str) -> Dict[str, str]:
        """Generate analytics from a configuration file."""
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        db_path = config["database_path"]
        conferences = config["conferences"]
        focus_country_code = config.get("focus_country_code", "IN")
        
        return cls.generate_batch_analytics(db_path, conferences, output_dir, focus_country_code)


class ValidationUtils:
    """Utilities for validating input data and configurations."""
    
    @staticmethod
    def validate_database(db_path: str) -> Dict[str, bool]:
        """Validate that the database exists and has required tables."""
        import sqlite3
        from pathlib import Path
        
        validation_results = {}
        
        # Check if file exists
        if not Path(db_path).exists():
            validation_results["database_exists"] = False
            return validation_results
        
        validation_results["database_exists"] = True
        
        required_tables = [
            'papers', 'authors', 'affiliations', 'institutions', 
            'countries', 'conferences', 'tracks', 'paper_authors',
            'paper_author_affiliations'
        ]
        
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
            validation_results["database_accessible"] = False
            validation_results["error"] = str(e)
        
        return validation_results
    
    @staticmethod
    def suggest_conferences(db_path: str) -> List[Dict]:
        """Suggest available conferences in the database."""
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        
        query = """
        SELECT 
            c.name as conference,
            c.year,
            COUNT(DISTINCT p.id) as paper_count,
            COUNT(DISTINCT a.id) as author_count
        FROM conferences c
        JOIN tracks t ON c.id = t.conference_id
        JOIN papers p ON t.id = p.track_id
        JOIN paper_authors pa ON p.id = pa.paper_id
        JOIN authors a ON pa.author_id = a.id
        GROUP BY c.name, c.year
        ORDER BY c.year DESC, c.name
        """
        
        cursor = conn.execute(query)
        suggestions = []
        
        for row in cursor.fetchall():
            suggestions.append({
                'conference': row[0],
                'year': row[1],
                'paper_count': row[2],
                'author_count': row[3]
            })
        
        conn.close()
        return suggestions
    
    @staticmethod
    def suggest_countries(db_path: str, limit: int = 20) -> List[Dict]:
        """Suggest countries based on number of affiliated authors."""
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        
        query = """
        SELECT 
            c.name as country,
            c.code as country_code,
            COUNT(DISTINCT a.id) as author_count,
            COUNT(DISTINCT p.id) as paper_count
        FROM countries c
        JOIN institutions i ON c.id = i.country_id
        JOIN affiliations af ON i.id = af.institution_id
        JOIN paper_author_affiliations paa ON af.id = paa.affiliation_id
        JOIN paper_authors pa ON paa.paper_author_id = pa.id
        JOIN authors a ON pa.author_id = a.id
        JOIN papers p ON pa.paper_id = p.id
        GROUP BY c.name, c.code
        ORDER BY author_count DESC
        LIMIT ?
        """
        
        cursor = conn.execute(query, (limit,))
        suggestions = []
        
        for row in cursor.fetchall():
            suggestions.append({
                'country': row[0],
                'country_code': row[1],
                'author_count': row[2],
                'paper_count': row[3]
            })
        
        conn.close()
        return suggestions


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Generate Analytics JSON from v2 Database Schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s generate data_v2/icml-v2.db ICML 2024 --country IN --output ./analytics/
  %(prog)s batch data_v2/icml-v2.db --config conferences.json --output ./analytics/
  %(prog)s validate data_v2/icml-v2.db
  %(prog)s suggest-conferences data_v2/icml-v2.db
  %(prog)s suggest-countries data_v2/icml-v2.db --limit 10
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate analytics for a single conference')
    generate_parser.add_argument('database', help='Path to SQLite database')
    generate_parser.add_argument('conference', help='Conference name (e.g., ICML)')
    generate_parser.add_argument('year', type=int, help='Conference year')
    generate_parser.add_argument('--country', default='IN', help='Focus country code (default: IN)')
    generate_parser.add_argument('--track', help='Track name filter (optional)')
    generate_parser.add_argument('--output', help='Output file path (optional)')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Generate analytics for multiple conferences')
    batch_parser.add_argument('database', help='Path to SQLite database')
    batch_parser.add_argument('--config', help='JSON config file with conference list')
    batch_parser.add_argument('--conferences', nargs='+', help='Conference specs: NAME:YEAR')
    batch_parser.add_argument('--country', default='IN', help='Focus country code (default: IN)')
    batch_parser.add_argument('--output', required=True, help='Output directory')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Generate analytics from config file')
    config_parser.add_argument('config_file', help='Path to configuration JSON file')
    config_parser.add_argument('output_dir', help='Output directory')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate database structure')
    validate_parser.add_argument('database', help='Path to SQLite database')
    
    # Suggest conferences command
    suggest_conf_parser = subparsers.add_parser('suggest-conferences', help='List available conferences')
    suggest_conf_parser.add_argument('database', help='Path to SQLite database')
    
    # Suggest countries command
    suggest_countries_parser = subparsers.add_parser('suggest-countries', help='Suggest focus countries')
    suggest_countries_parser.add_argument('database', help='Path to SQLite database')
    suggest_countries_parser.add_argument('--limit', type=int, default=20, help='Number of suggestions')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        try:
            output_path = args.output
            if not output_path:
                # Generate default output path
                filename = f"{args.conference.lower()}-{args.year}-analytics.json"
                if args.track:
                    filename = f"{args.conference.lower()}-{args.year}-{args.track.lower()}-analytics.json"
                output_path = filename
            
            analytics = AnalyticsRunner.generate_single_analytics(
                db_path=args.database,
                conference_name=args.conference,
                year=args.year,
                focus_country_code=args.country,
                track_name=args.track,
                output_path=output_path
            )
            
            print(f"Analytics generated successfully!")
            print(f"Output file: {output_path}")
            print(f"Focus country: {COUNTRY_CODE_MAP.get(args.country, args.country)}")
            print(f"Total papers: {analytics['globalStats']['totalPapers']}")
            print(f"Focus country papers: {analytics['focusCountrySummary']['paper_count']}")
            print(f"Focus country rank: {analytics['focusCountrySummary']['rank']}")
            
        except Exception as e:
            logger.error(f"Analytics generation failed: {e}")
            sys.exit(1)
    
    elif args.command == 'batch':
        try:
            conferences = []
            
            if args.config:
                with open(args.config, 'r') as f:
                    config_data = json.load(f)
                    conferences = config_data.get('conferences', [])
            elif args.conferences:
                for conf_spec in args.conferences:
                    if ':' in conf_spec:
                        name, year = conf_spec.split(':', 1)
                        conferences.append({
                            'name': name,
                            'year': int(year)
                        })
                    else:
                        logger.error(f"Invalid conference spec: {conf_spec}. Use NAME:YEAR format.")
                        sys.exit(1)
            else:
                logger.error("Either --config or --conferences must be specified")
                sys.exit(1)
            
            output_files = AnalyticsRunner.generate_batch_analytics(
                db_path=args.database,
                conferences=conferences,
                output_dir=args.output,
                focus_country_code=args.country
            )
            
            print(f"Batch analytics generation completed!")
            print(f"Generated {len(output_files)} analytics files:")
            for conf, filepath in output_files.items():
                print(f"  {conf}: {filepath}")
                
        except Exception as e:
            logger.error(f"Batch analytics generation failed: {e}")
            sys.exit(1)
    
    elif args.command == 'config':
        try:
            output_files = AnalyticsRunner.generate_from_config(
                args.config_file, args.output_dir
            )
            
            print(f"Config-based analytics generation completed!")
            print(f"Generated {len(output_files)} analytics files:")
            for conf, filepath in output_files.items():
                print(f"  {conf}: {filepath}")
                
        except Exception as e:
            logger.error(f"Config-based analytics generation failed: {e}")
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
    
    elif args.command == 'suggest-conferences':
        try:
            suggestions = ValidationUtils.suggest_conferences(args.database)
            
            print("Available conferences:")
            print(f"{'Conference':<15} {'Year':<6} {'Papers':<8} {'Authors':<8}")
            print("-" * 39)
            
            for suggestion in suggestions:
                print(f"{suggestion['conference']:<15} {suggestion['year']:<6} "
                      f"{suggestion['paper_count']:<8} {suggestion['author_count']:<8}")
                
        except Exception as e:
            logger.error(f"Conference suggestion failed: {e}")
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
            logger.error(f"Country suggestion failed: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
