#!/usr/bin/env python3
"""
Batch Paperlist Importer

Recursively processes all JSON files in a directory, combining all data into
a shared database with individual log files for each JSON file.

Usage:
    python batch_importer.py /path/to/json/folder [options]

Features:
    - Recursive JSON file discovery
    - Shared database for all JSON files (or individual databases)
    - Individual log files for each processing session
    - Parallel processing support
    - Progress tracking across all files
    - Error isolation (one failed file doesn't stop others)
"""

import os
import sys
import argparse
import json
import re
import time
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime
from sqlalchemy import create_engine, text

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ImporterConfig
from pipeline.paperlist_importer import PaperlistsTransformer


class BatchImporter:
    """Batch processor for multiple JSON paperlist files."""
    
    def __init__(self, config: ImporterConfig = None, shared_database: Optional[str] = None, force_restart: bool = False):
        self.config = config or ImporterConfig()
        self.shared_database = shared_database
        self.force_restart = force_restart
        self.setup_logging()
        self.stats = {
            'files_found': 0,
            'files_processed': 0,
            'files_failed': 0,
            'total_papers': 0,
            'start_time': time.time()
        }
        
        # Handle force restart if requested
        if self.force_restart:
            self.perform_force_restart()
    
    def setup_logging(self):
        """Setup main batch processing logger."""
        # Create logs directory if it doesn't exist
        log_dir = Path(self.config.log_directory)
        log_dir.mkdir(exist_ok=True)
        
        # Create batch-specific log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"batch_importer_{timestamp}.log"
        
        # Setup logger
        self.logger = logging.getLogger("batch_importer")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Batch importer started. Logs: {log_file}")
    
    def perform_force_restart(self):
        """Perform force restart by cleaning up existing databases and logs."""
        self.logger.info("🔄 Force restart requested - cleaning up existing data...")
        
        try:
            # Clean up databases if configured
            if self.config.cleanup_databases_on_restart:
                self._cleanup_databases()
            
            # Clean up logs if configured
            if self.config.cleanup_logs_on_restart:
                self._cleanup_logs()
                
            self.logger.info("✅ Force restart cleanup completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error during force restart cleanup: {e}")
            raise
    
    def _cleanup_databases(self):
        """Clean up existing database files."""
        db_patterns = ["*.db", "*.sqlite", "*.sqlite3"]
        cleaned_count = 0
        
        # Clean up shared database if specified
        if self.shared_database:
            db_path = Path(self.shared_database)
            if db_path.exists():
                try:
                    db_path.unlink()
                    self.logger.info(f"🗑️  Deleted shared database: {db_path}")
                    cleaned_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to delete {db_path}: {e}")
        
        # Clean up databases in common locations
        common_db_locations = [
            Path.cwd(),
            Path(self.config.log_directory).parent if hasattr(self.config, 'log_directory') else Path.cwd(),
            Path("data"),
            Path("data_v2"),
            Path("processed")
        ]
        
        for location in common_db_locations:
            if location.exists() and location.is_dir():
                for pattern in db_patterns:
                    for db_file in location.glob(pattern):
                        try:
                            db_file.unlink()
                            self.logger.info(f"🗑️  Deleted database: {db_file}")
                            cleaned_count += 1
                        except Exception as e:
                            self.logger.warning(f"Failed to delete {db_file}: {e}")
        
        self.logger.info(f"🗑️  Cleaned up {cleaned_count} database files")
    
    def _cleanup_logs(self):
        """Clean up existing log directories."""
        log_locations = [
            Path(self.config.log_directory),
            Path("logs"),
            Path("custom_logs"),
            Path("processed/logs")
        ]
        
        cleaned_count = 0
        for log_dir in log_locations:
            if log_dir.exists() and log_dir.is_dir():
                try:
                    shutil.rmtree(log_dir)
                    self.logger.info(f"🗑️  Deleted log directory: {log_dir}")
                    cleaned_count += 1
                    # Recreate the main log directory
                    if str(log_dir) == self.config.log_directory:
                        log_dir.mkdir(exist_ok=True)
                except Exception as e:
                    self.logger.warning(f"Failed to delete log directory {log_dir}: {e}")
        
        self.logger.info(f"🗑️  Cleaned up {cleaned_count} log directories")
    
    def flush_database(self, db_file: str):
        """Flush and optimize the database between conference processing."""
        if not self.config.enable_db_flush_between_conferences:
            return
            
        self.logger.info(f"🔄 Flushing database: {db_file}")
        flush_start_time = time.time()
        
        try:
            # Create engine for database operations
            engine = create_engine(f"sqlite:///{db_file}", echo=False)
            
            with engine.connect() as conn:
                # Execute VACUUM to optimize database
                conn.execute(text("VACUUM"))
                
                # Execute ANALYZE to update statistics
                conn.execute(text("ANALYZE"))
                
                # Commit changes
                conn.commit()
            
            # Close engine
            engine.dispose()
            
            flush_duration = time.time() - flush_start_time
            self.logger.info(f"✅ Database flushed successfully in {flush_duration:.2f}s")
            
        except Exception as e:
            flush_duration = time.time() - flush_start_time
            self.logger.warning(f"⚠️  Database flush failed after {flush_duration:.2f}s: {e}")
    
    def wait_between_conferences(self):
        """Wait between conference processing if configured."""
        if self.config.inter_conference_delay_seconds > 0:
            self.logger.info(f"⏳ Waiting {self.config.inter_conference_delay_seconds}s before next conference...")
            time.sleep(self.config.inter_conference_delay_seconds)
            self.logger.info("✅ Wait period completed")
    
    def find_json_files(self, directory: str) -> List[Path]:
        """Recursively find all JSON files in the directory."""
        directory_path = Path(directory)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
        
        # Find all JSON files recursively
        json_files = list(directory_path.rglob("*.json"))
        
        # Filter out files that might not be paperlist data
        valid_files = []
        for json_file in json_files:
            try:
                # Quick validation - check if it's a valid JSON and has expected structure
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Basic validation - should be a list of dictionaries with paper-like structure
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], dict) and any(key in data[0] for key in ['id', 'title', 'author']):
                        valid_files.append(json_file)
                        self.logger.info(f"Found valid JSON file: {json_file} ({len(data)} records)")
                    else:
                        self.logger.warning(f"Skipping JSON file (invalid structure): {json_file}")
                else:
                    self.logger.warning(f"Skipping JSON file (empty or invalid): {json_file}")
                    
            except (json.JSONDecodeError, UnicodeDecodeError, Exception) as e:
                self.logger.warning(f"Skipping invalid JSON file {json_file}: {e}")
        
        self.stats['files_found'] = len(valid_files)
        self.logger.info(f"Found {len(valid_files)} valid JSON files to process")
        
        return valid_files
    
    def extract_year_from_filename(self, json_file: Path) -> Optional[int]:
        """Extract year from filename using regex pattern \\d{4}."""
        filename = json_file.stem  # Get filename without extension
        
        # Look for 4-digit year pattern in filename
        year_match = re.search(r'\d{4}', filename)
        if year_match:
            year = int(year_match.group())
            # Validate that it's a reasonable conference year (e.g., 2000-2030)
            if 1900 <= year <= 2030:
                self.logger.info(f"Extracted year {year} from filename: {filename}")
                return year
            else:
                self.logger.warning(f"Found year {year} in filename {filename}, but it's outside reasonable range (1900-2030)")
        
        self.logger.warning(f"Could not extract valid year from filename: {filename}")
        return None
    
    def extract_conference_from_filename(self, json_file: Path) -> Optional[str]:
        """Extract conference name from filename using configured mappings."""
        filename = json_file.stem.lower()  # Get filename without extension, lowercase
        
        # Remove year and common separators to get clean conference name
        filename_clean = re.sub(r'\d{4}', '', filename).strip('_-. ')
        
        # Check against configured filename-to-conference mapping
        for key, conference in self.config.filename_to_conference.items():
            if key in filename_clean:
                self.logger.info(f"Extracted conference '{conference}' from filename: {json_file.stem}")
                return conference
        
        # Try partial matches for robustness
        for key, conference in self.config.filename_to_conference.items():
            if key in filename or filename.startswith(key):
                self.logger.info(f"Extracted conference '{conference}' from filename (partial match): {json_file.stem}")
                return conference
        
        self.logger.warning(f"Could not extract conference name from filename: {json_file.stem}")
        self.logger.warning(f"Available conference mappings: {list(self.config.filename_to_conference.keys())}")
        return None
    
    def generate_output_paths(self, json_file: Path, output_dir: Optional[str] = None, 
                            shared_db_file: Optional[str] = None) -> Tuple[str, str]:
        """Generate database and log file paths for a JSON file."""
        # Use the JSON file's stem (filename without extension) for naming logs
        relative_path = json_file.relative_to(json_file.parents[-2] if len(json_file.parents) > 1 else json_file.parent)
        safe_name = str(relative_path.with_suffix('')).replace('/', '_').replace('\\', '_')
        
        # Output directory
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = json_file.parent / "processed"
        
        output_path.mkdir(exist_ok=True)
        
        # Database file - use shared database if provided
        if shared_db_file:
            db_file = shared_db_file
        else:
            db_file = output_path / "combined_papers.db"
        
        # Log directory for this specific file
        log_dir = output_path / "logs" / safe_name
        log_dir.mkdir(parents=True, exist_ok=True)
        
        return str(db_file), str(log_dir)
    
    def process_single_file(self, json_file: Path, output_dir: Optional[str] = None, 
                          custom_config: Optional[ImporterConfig] = None) -> Dict:
        """Process a single JSON file with isolated logging and shared database."""
        start_time = time.time()
        result = {
            'file': str(json_file),
            'success': False,
            'papers_processed': 0,
            'error': None,
            'duration': 0,
            'database_file': None,
            'log_directory': None
        }
        
        try:
            # Generate output paths - use shared database if specified
            db_file, log_dir = self.generate_output_paths(json_file, output_dir, self.shared_database)
            result['database_file'] = db_file
            result['log_directory'] = log_dir
            
            self.logger.info(f"Processing {json_file}")
            self.logger.info(f"  Database: {db_file}")
            self.logger.info(f"  Logs: {log_dir}")
            
            # Create file-specific configuration
            file_config = custom_config or ImporterConfig()
            file_config.database_url = f"sqlite:///{db_file}"
            file_config.log_directory = log_dir
            
            # Extract year and conference from filename
            conference_year = self.extract_year_from_filename(json_file)
            conference_name = self.extract_conference_from_filename(json_file)
            
            if conference_year:
                self.logger.info(f"Using extracted year {conference_year} for conference data")
            if conference_name:
                self.logger.info(f"Using extracted conference '{conference_name}' for conference data")
            else:
                self.logger.warning(f"Could not extract conference from filename {json_file.stem}, will use fallback detection")
            
            # Load JSON data
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("JSON file must contain a list of paper records")
            
            # Create transformer with file-specific configuration, extracted year and conference
            transformer = PaperlistsTransformer(
                config=file_config, 
                conference_year=conference_year,
                conference_name=conference_name
            )
            
            # Process the data
            transformer.transform_paperlists_data(data)
            
            # Get processing statistics from transformer's stats attribute
            result['papers_processed'] = transformer.stats.get('papers_processed', 0)
            result['success'] = True
            
            self.logger.info(f"Successfully processed {json_file}: {result['papers_processed']} papers")
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Failed to process {json_file}: {e}")
        
        finally:
            result['duration'] = time.time() - start_time
        
        return result
    
    def process_files_sequential(self, json_files: List[Path], output_dir: Optional[str] = None) -> List[Dict]:
        """Process files sequentially with database flushing and wait periods between conferences."""
        results = []
        
        for i, json_file in enumerate(json_files, 1):
            self.logger.info(f"Processing file {i}/{len(json_files)}: {json_file.name}")
            
            result = self.process_single_file(json_file, output_dir)
            results.append(result)
            
            # Update stats
            if result['success']:
                self.stats['files_processed'] += 1
                self.stats['total_papers'] += result['papers_processed']
                
                # Flush database after successful processing
                if result.get('database_file'):
                    self.flush_database(result['database_file'])
                
            else:
                self.stats['files_failed'] += 1
            
            # Progress update
            elapsed = time.time() - self.stats['start_time']
            avg_time = elapsed / i
            remaining = (len(json_files) - i) * avg_time
            
            self.logger.info(f"Progress: {i}/{len(json_files)} files, "
                           f"Elapsed: {elapsed:.1f}s, "
                           f"Estimated remaining: {remaining:.1f}s")
            
            # Wait between conferences if not the last file
            if i < len(json_files):
                self.wait_between_conferences()
        
        return results
    
    def process_files_parallel(self, json_files: List[Path], output_dir: Optional[str] = None, 
                             max_workers: int = 2) -> List[Dict]:
        """Process files in parallel (for smaller files)."""
        results = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.process_single_file, json_file, output_dir): json_file 
                for json_file in json_files
            }
            
            # Process completed tasks
            for future in as_completed(future_to_file):
                json_file = future_to_file[future]
                completed += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Update stats
                    if result['success']:
                        self.stats['files_processed'] += 1
                        self.stats['total_papers'] += result['papers_processed']
                    else:
                        self.stats['files_failed'] += 1
                    
                    self.logger.info(f"Completed {completed}/{len(json_files)}: {json_file.name}")
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error processing {json_file}: {e}")
                    results.append({
                        'file': str(json_file),
                        'success': False,
                        'error': str(e),
                        'papers_processed': 0,
                        'duration': 0
                    })
                    self.stats['files_failed'] += 1
        
        return results
    
    def generate_summary_report(self, results: List[Dict]) -> str:
        """Generate a summary report of the batch processing."""
        total_duration = time.time() - self.stats['start_time']
        
        # Calculate statistics
        successful_files = [r for r in results if r['success']]
        failed_files = [r for r in results if not r['success']]
        
        total_papers = sum(r['papers_processed'] for r in successful_files)
        avg_papers_per_file = total_papers / len(successful_files) if successful_files else 0
        avg_processing_time = sum(r['duration'] for r in successful_files) / len(successful_files) if successful_files else 0
        
        report = f"""
📊 BATCH PROCESSING SUMMARY
{'=' * 50}

📁 Files Processed:
  Total files found: {self.stats['files_found']}
  Successfully processed: {len(successful_files)}
  Failed: {len(failed_files)}
  Success rate: {len(successful_files)/len(results)*100:.1f}%

📄 Papers Processed:
  Total papers: {total_papers:,}
  Average per file: {avg_papers_per_file:.1f}

⏱️  Performance:
  Total processing time: {total_duration:.1f} seconds
  Average time per file: {avg_processing_time:.1f} seconds
  Papers per second: {total_papers/total_duration:.2f}

✅ Successful Files:
"""
        
        for result in successful_files:
            report += f"  ✓ {Path(result['file']).name}: {result['papers_processed']} papers ({result['duration']:.1f}s)\n"
        
        if failed_files:
            report += f"\n❌ Failed Files:\n"
            for result in failed_files:
                report += f"  ✗ {Path(result['file']).name}: {result['error']}\n"
        
        report += f"\n📂 Output Locations:\n"
        for result in successful_files:
            if result.get('database_file'):
                report += f"  DB: {result['database_file']}\n"
                report += f"  Logs: {result['log_directory']}\n"
        
        return report
    
    def run(self, directory: str, output_dir: Optional[str] = None, 
            parallel: bool = False, max_workers: int = 2) -> List[Dict]:
        """Main entry point for batch processing."""
        self.logger.info(f"Starting batch import from directory: {directory}")
        
        try:
            # Find JSON files
            json_files = self.find_json_files(directory)
            
            if not json_files:
                self.logger.warning("No valid JSON files found")
                return []
            
            # Process files
            if parallel and len(json_files) > 1:
                self.logger.info(f"Processing {len(json_files)} files in parallel (max_workers={max_workers})")
                results = self.process_files_parallel(json_files, output_dir, max_workers)
            else:
                self.logger.info(f"Processing {len(json_files)} files sequentially")
                results = self.process_files_sequential(json_files, output_dir)
            
            # Generate and log summary
            summary = self.generate_summary_report(results)
            self.logger.info(summary)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            raise


def main():
    """Command line interface for batch importer."""
    parser = argparse.ArgumentParser(
        description="Batch process JSON paperlist files recursively",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all JSON files in a directory
  python batch_importer.py /path/to/json/files
  
  # Process with custom output directory
  python batch_importer.py /path/to/json/files --output /path/to/output
  
  # Process in parallel (for smaller files)
  python batch_importer.py /path/to/json/files --parallel --max-workers 4
  
  # Force restart - delete all existing data and start fresh
  python batch_importer.py /path/to/json/files --force-restart
  
  # Custom inter-conference delay and disable database flushing
  python batch_importer.py /path/to/json/files --inter-conference-delay 5.0 --disable-db-flush
  
  # Custom configuration with force restart
  python batch_importer.py /path/to/json/files --config custom_config.json --force-restart
        """
    )
    
    parser.add_argument(
        "directory",
        help="Directory to search for JSON files (recursive)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output directory for databases and logs (default: processed/ in each JSON file's directory)"
    )
    
    parser.add_argument(
        "--database", "-d",
        help="Path to shared database file (default: combined_papers.db in output directory)"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration JSON file"
    )
    
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Process files in parallel (use for smaller files)"
    )
    
    parser.add_argument(
        "--max-workers", "-w",
        type=int,
        default=2,
        help="Maximum number of parallel workers (default: 2)"
    )
    
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--force-restart", "-f",
        action="store_true",
        help="Delete all existing databases and logs before starting (use with caution)"
    )
    
    parser.add_argument(
        "--inter-conference-delay",
        type=float,
        default=None,
        help="Seconds to wait between processing conferences (default: from config, 3.0s)"
    )
    
    parser.add_argument(
        "--disable-db-flush",
        action="store_true",
        help="Disable database flushing between conferences"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = ImporterConfig()
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config_data = json.load(f)
                # Update config with loaded data
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
        except Exception as e:
            print(f"Error loading config file: {e}")
            sys.exit(1)
    
    # Apply CLI argument overrides to config
    if args.inter_conference_delay is not None:
        config.inter_conference_delay_seconds = args.inter_conference_delay
    
    if args.disable_db_flush:
        config.enable_db_flush_between_conferences = False
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Show configuration summary
    print(f"🔧 Configuration Summary:")
    print(f"  Database flushing: {'enabled' if config.enable_db_flush_between_conferences else 'disabled'}")
    print(f"  Inter-conference delay: {config.inter_conference_delay_seconds}s")
    print(f"  Force restart: {'yes' if args.force_restart else 'no'}")
    print(f"  Shared database: {args.database or 'auto-generated'}")
    print(f"  Log level: {args.log_level}")
    
    # Create and run batch importer
    try:
        batch_importer = BatchImporter(config, shared_database=args.database, force_restart=args.force_restart)
        results = batch_importer.run(
            directory=args.directory,
            output_dir=args.output,
            parallel=args.parallel,
            max_workers=args.max_workers
        )
        
        # Exit with appropriate code
        failed_count = sum(1 for r in results if not r['success'])
        if failed_count > 0:
            print(f"\nWarning: {failed_count} files failed to process")
            sys.exit(1)
        else:
            print(f"\nSuccess: All {len(results)} files processed successfully")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nBatch processing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Batch processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
