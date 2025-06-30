#!/usr/bin/env python3
"""
Test script to verify filename-based conference detection functionality.

This script tests the enhanced batch importer and processor with conference
detection from filenames.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import ImporterConfig
from pipeline.batch_importer import BatchImporter

def create_test_data():
    """Create sample test data for different conferences."""
    
    # Sample paper data structure
    base_paper = {
        "id": "test_paper_001",
        "title": "A Test Paper for Conference Detection",
        "author": "John Doe;Jane Smith",
        "status": "accepted",
        "track": "main",
        "primary_area": "Machine Learning",
        "abstract": "This is a test paper to verify conference detection functionality.",
        "keywords": "machine learning;test;conference detection",
        "bibtex": "@inproceedings{test2024paper,title={A Test Paper},year={2024}}",
        "author_num": 2,
        "aff": "University A;University B",
        "aff_unique_norm": "University A;University B",
        "aff_country_unique": "USA;Canada"
    }
    
    # Test data for different conferences
    test_files = {
        "nips2024.json": {
            "conference": "NeurIPS",
            "papers": [
                {**base_paper, "id": "neurips_paper_001", "title": "NeurIPS Test Paper 1"},
                {**base_paper, "id": "neurips_paper_002", "title": "NeurIPS Test Paper 2"}
            ]
        },
        "icml2024.json": {
            "conference": "ICML", 
            "papers": [
                {**base_paper, "id": "icml_paper_001", "title": "ICML Test Paper 1"},
                {**base_paper, "id": "icml_paper_002", "title": "ICML Test Paper 2"}
            ]
        },
        "iclr2025.json": {
            "conference": "ICLR",
            "papers": [
                {**base_paper, "id": "iclr_paper_001", "title": "ICLR Test Paper 1"},
                {**base_paper, "id": "iclr_paper_002", "title": "ICLR Test Paper 2"}
            ]
        },
        "unknown_conference_2024.json": {
            "conference": None,  # Should fall back to bibtex detection
            "papers": [
                {**base_paper, "id": "unknown_paper_001", "title": "Unknown Conference Paper"}
            ]
        }
    }
    
    return test_files

def test_conference_extraction():
    """Test conference extraction from filenames."""
    print("🧪 Testing Conference Extraction from Filenames")
    print("=" * 60)
    
    # Create test configuration
    config = ImporterConfig()
    batch_importer = BatchImporter(config)
    
    # Test cases
    test_cases = [
        ("nips2024.json", "NeurIPS", 2024),
        ("neurips2025.json", "NeurIPS", 2025),
        ("icml2024.json", "ICML", 2024),
        ("iclr2025.json", "ICLR", 2025),
        ("cvpr_2024.json", "CVPR", 2024),
        ("unknown_conf_2024.json", None, 2024),
        ("no_year_icml.json", "ICML", None),
        ("invalid_year_icml_9999.json", "ICML", None),
    ]
    
    print("Testing filename parsing:")
    for filename, expected_conf, expected_year in test_cases:
        test_path = Path(filename)
        
        # Test conference extraction
        extracted_conf = batch_importer.extract_conference_from_filename(test_path)
        
        # Test year extraction
        extracted_year = batch_importer.extract_year_from_filename(test_path)
        
        # Validate results
        conf_status = "✅" if extracted_conf == expected_conf else "❌"
        year_status = "✅" if extracted_year == expected_year else "❌"
        
        print(f"  {filename}")
        print(f"    Conference: {extracted_conf} (expected: {expected_conf}) {conf_status}")
        print(f"    Year: {extracted_year} (expected: {expected_year}) {year_status}")
        print()

def test_batch_processing():
    """Test batch processing with conference detection."""
    print("🚀 Testing Batch Processing with Conference Detection")
    print("=" * 60)
    
    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test data files
        test_data = create_test_data()
        
        print("Creating test files:")
        for filename, data in test_data.items():
            file_path = temp_path / filename
            with open(file_path, 'w') as f:
                json.dump(data["papers"], f, indent=2)
            print(f"  ✅ Created {filename} with {len(data['papers'])} papers")
        
        print(f"\nTest files created in: {temp_dir}")
        
        # Create configuration for testing
        config = ImporterConfig()
        config.log_directory = str(temp_path / "logs")
        
        # Create batch importer
        batch_importer = BatchImporter(config, shared_database=str(temp_path / "test_papers.db"))
        
        print(f"\nProcessing files...")
        try:
            # Run batch processing
            results = batch_importer.run(
                directory=str(temp_dir),
                output_dir=str(temp_path / "output"),
                parallel=False
            )
            
            print(f"\n📊 Processing Results:")
            print(f"  Total files processed: {len(results)}")
            
            successful_results = [r for r in results if r['success']]
            failed_results = [r for r in results if not r['success']]
            
            print(f"  Successful: {len(successful_results)}")
            print(f"  Failed: {len(failed_results)}")
            
            if successful_results:
                total_papers = sum(r['papers_processed'] for r in successful_results)
                print(f"  Total papers processed: {total_papers}")
                
                print(f"\n✅ Successful files:")
                for result in successful_results:
                    filename = Path(result['file']).name
                    papers = result['papers_processed']
                    duration = result['duration']
                    print(f"    {filename}: {papers} papers ({duration:.2f}s)")
            
            if failed_results:
                print(f"\n❌ Failed files:")
                for result in failed_results:
                    filename = Path(result['file']).name
                    error = result['error']
                    print(f"    {filename}: {error}")
            
            # Check if database was created
            db_path = temp_path / "test_papers.db"
            if db_path.exists():
                print(f"\n📁 Database created: {db_path}")
                print(f"   Size: {db_path.stat().st_size} bytes")
            else:
                print(f"\n❌ Database not found at: {db_path}")
                
        except Exception as e:
            print(f"\n❌ Batch processing failed: {e}")
            import traceback
            traceback.print_exc()

def test_conference_mapping():
    """Test the conference mapping configuration."""
    print("🗺️  Testing Conference Mapping Configuration")
    print("=" * 60)
    
    config = ImporterConfig()
    
    print("Available conference mappings:")
    for key, conference in config.filename_to_conference.items():
        full_name = config.conference_full_names.get(conference, conference)
        print(f"  '{key}' → {conference} ({full_name})")
    
    print(f"\nTotal mappings: {len(config.filename_to_conference)}")

def main():
    """Run all tests."""
    print("🧪 Conference Detection Test Suite")
    print("=" * 60)
    print()
    
    try:
        # Test 1: Conference mapping configuration
        test_conference_mapping()
        print()
        
        # Test 2: Filename extraction
        test_conference_extraction()
        print()
        
        # Test 3: Batch processing (commented out for now to avoid creating files)
        # Uncomment the line below to test actual batch processing
        # test_batch_processing()
        
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
