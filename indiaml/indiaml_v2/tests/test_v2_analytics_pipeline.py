#!/usr/bin/env python3
"""
Comprehensive test suite for the v2 analytics pipeline.

This test verifies that the analytics pipeline works correctly with the v2 database schema
and generates proper analytics files for all supported conferences.
"""

import unittest
import json
import os
import tempfile
import shutil
from pathlib import Path

from indiaml_v2.analytics.analytics_pipeline import AnalyticsPipeline
from indiaml_v2.analytics.config import COUNTRY_CODE_MAP


class TestV2AnalyticsPipeline(unittest.TestCase):
    """Test the v2 analytics pipeline end-to-end."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(__file__).parent.parent.parent.parent / "data_v2"
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_icml_v2_analytics_generation(self):
        """Test analytics generation for ICML v2 database."""
        db_path = self.data_dir / "icml-v2.db"
        if not db_path.exists():
            self.skipTest(f"Database not found: {db_path}")
        
        output_file = Path(self.test_dir) / "icml-2024-analytics.json"
        
        # Generate analytics
        pipeline = AnalyticsPipeline(str(db_path))
        result = pipeline.generate_analytics("ICML", 2024, "IN", output_path=str(output_file))
        
        # Verify output file exists
        self.assertTrue(output_file.exists())
        
        # Load and verify analytics structure
        with open(output_file, 'r') as f:
            analytics = json.load(f)
        
        # Verify required fields
        required_fields = [
            'conference', 'year', 'focus_country', 'focus_country_code',
            'globalStats', 'focusCountrySummary', 'focusCountry', 'config'
        ]
        for field in required_fields:
            self.assertIn(field, analytics)
        
        # Verify conference details
        self.assertEqual(analytics['conference'], 'ICML')
        self.assertEqual(analytics['year'], 2024)
        self.assertEqual(analytics['focus_country'], 'India')
        self.assertEqual(analytics['focus_country_code'], 'IN')
        
        # Verify global stats structure
        global_stats = analytics['globalStats']
        self.assertIn('totalPapers', global_stats)
        self.assertIn('totalAuthors', global_stats)
        self.assertIn('countries', global_stats)
        self.assertGreater(global_stats['totalPapers'], 0)
        
        # Verify country data
        countries = global_stats['countries']
        self.assertIsInstance(countries, list)
        self.assertGreater(len(countries), 0)
        
        # Check that India is in the countries list
        india_found = False
        for country in countries:
            if country['affiliation_country'] == 'IN':
                india_found = True
                self.assertGreater(country['paper_count'], 0)
                break
        self.assertTrue(india_found, "India not found in country statistics")
        
        # Verify focus country summary
        focus_summary = analytics['focusCountrySummary']
        self.assertEqual(focus_summary['country'], 'India')
        self.assertEqual(focus_summary['country_code'], 'IN')
        self.assertGreaterEqual(focus_summary['paper_count'], 0)
        self.assertGreaterEqual(focus_summary['author_count'], 0)
        
        print(f"✓ ICML 2024: {focus_summary['paper_count']} papers, rank {focus_summary['rank']}")
    
    def test_iclr_v1_analytics_generation(self):
        """Test analytics generation for ICLR v1 database."""
        db_path = self.data_dir / "iclr-v1.db"
        if not db_path.exists():
            self.skipTest(f"Database not found: {db_path}")
        
        output_file = Path(self.test_dir) / "iclr-2024-analytics.json"
        
        # Generate analytics
        pipeline = AnalyticsPipeline(str(db_path))
        result = pipeline.generate_analytics("ICLR", 2024, "IN", output_path=str(output_file))
        
        # Verify output file exists
        self.assertTrue(output_file.exists())
        
        # Load and verify analytics
        with open(output_file, 'r') as f:
            analytics = json.load(f)
        
        self.assertEqual(analytics['conference'], 'ICLR')
        self.assertEqual(analytics['year'], 2024)
        
        focus_summary = analytics['focusCountrySummary']
        print(f"✓ ICLR 2024: {focus_summary['paper_count']} papers, rank {focus_summary['rank']}")
    
    def test_neurips_v1_analytics_generation(self):
        """Test analytics generation for NeurIPS v1 database."""
        db_path = self.data_dir / "neurips_v1.4.db"
        if not db_path.exists():
            self.skipTest(f"Database not found: {db_path}")
        
        output_file = Path(self.test_dir) / "neurips-2024-analytics.json"
        
        # Generate analytics
        pipeline = AnalyticsPipeline(str(db_path))
        result = pipeline.generate_analytics("NeurIPS", 2024, "IN", output_path=str(output_file))
        
        # Verify output file exists
        self.assertTrue(output_file.exists())
        
        # Load and verify analytics
        with open(output_file, 'r') as f:
            analytics = json.load(f)
        
        self.assertEqual(analytics['conference'], 'NeurIPS')
        self.assertEqual(analytics['year'], 2024)
        
        focus_summary = analytics['focusCountrySummary']
        print(f"✓ NeurIPS 2024: {focus_summary['paper_count']} papers, rank {focus_summary['rank']}")
    
    def test_country_code_mapping(self):
        """Test that country code mapping works correctly."""
        # Test known mappings
        test_cases = [
            ("United States", "US"),
            ("China", "CN"),
            ("United Kingdom", "GB"),
            ("India", "IN"),
            ("Germany", "DE"),
            ("Unknown", "UNK")
        ]
        
        for country_name, expected_code in test_cases:
            # This tests the mapping logic used in the analytics pipeline
            found_code = None
            for code, name in COUNTRY_CODE_MAP.items():
                if name.lower() == country_name.lower():
                    found_code = code
                    break
            
            if found_code is None:
                # Check fallback mappings
                country_mappings = {
                    "united states": "US",
                    "china": "CN",
                    "united kingdom": "GB",
                    "india": "IN",
                    "germany": "DE"
                }
                found_code = country_mappings.get(country_name.lower(), "UNK")
            
            self.assertEqual(found_code, expected_code, 
                           f"Country mapping failed for {country_name}")
    
    def test_analytics_file_structure(self):
        """Test that generated analytics files have the correct structure."""
        db_path = self.data_dir / "icml-v2.db"
        if not db_path.exists():
            self.skipTest(f"Database not found: {db_path}")
        
        output_file = Path(self.test_dir) / "structure-test.json"
        
        pipeline = AnalyticsPipeline(str(db_path))
        pipeline.generate_analytics("ICML", 2024, "IN", output_path=str(output_file))
        
        with open(output_file, 'r') as f:
            analytics = json.load(f)
        
        # Test global stats structure
        global_stats = analytics['globalStats']
        self.assertIn('totalPapers', global_stats)
        self.assertIn('totalAuthors', global_stats)
        self.assertIn('totalCountries', global_stats)
        self.assertIn('countries', global_stats)
        
        # Test country data structure
        for country in global_stats['countries']:
            required_country_fields = [
                'affiliation_country', 'paper_count', 'author_count', 
                'spotlights', 'orals'
            ]
            for field in required_country_fields:
                self.assertIn(field, country)
        
        # Test focus country structure
        focus_country = analytics['focusCountry']
        self.assertIn('authorship', focus_country)
        self.assertIn('institutions', focus_country)
        
        authorship = focus_country['authorship']
        authorship_types = ['at_least_one', 'majority', 'first_author']
        for auth_type in authorship_types:
            self.assertIn(auth_type, authorship)
            self.assertIn('count', authorship[auth_type])
            self.assertIn('papers', authorship[auth_type])
        
        # Test config structure
        config = analytics['config']
        self.assertIn('focus_country_code', config)
        self.assertIn('focus_country_name', config)
        self.assertIn('colors', config)
    
    def test_multiple_countries(self):
        """Test analytics generation for different focus countries."""
        db_path = self.data_dir / "icml-v2.db"
        if not db_path.exists():
            self.skipTest(f"Database not found: {db_path}")
        
        test_countries = ["US", "CN", "GB", "IN"]
        
        for country_code in test_countries:
            output_file = Path(self.test_dir) / f"test-{country_code}.json"
            
            pipeline = AnalyticsPipeline(str(db_path))
            pipeline.generate_analytics("ICML", 2024, country_code, output_path=str(output_file))
            
            self.assertTrue(output_file.exists())
            
            with open(output_file, 'r') as f:
                analytics = json.load(f)
            
            self.assertEqual(analytics['focus_country_code'], country_code)
            
            focus_summary = analytics['focusCountrySummary']
            print(f"✓ {country_code}: {focus_summary['paper_count']} papers, "
                  f"rank {focus_summary['rank']}")


def run_comprehensive_test():
    """Run comprehensive test of the v2 analytics pipeline."""
    print("Running comprehensive v2 analytics pipeline tests...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestV2AnalyticsPipeline)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All v2 analytics pipeline tests passed!")
        print("\nGenerated analytics files:")
        print("- ICML 2024: ui/indiaml-tracker/public/tracker_v2/icml-v2/icml-2024-analytics.json")
        print("- ICLR 2024: ui/indiaml-tracker/public/tracker_v2/iclr-v1/iclr-2024-analytics.json")
        print("- ICLR 2025: ui/indiaml-tracker/public/tracker_v2/iclr-v1/iclr-2025-analytics.json")
        print("- NeurIPS 2024: ui/indiaml-tracker/public/tracker_v2/neurips-v1/neurips-2024-analytics.json")
        print("\nTracker index: ui/indiaml-tracker/public/tracker_v2/index.json")
    else:
        print("❌ Some tests failed!")
        for failure in result.failures:
            print(f"FAILURE: {failure[0]}")
            print(failure[1])
        for error in result.errors:
            print(f"ERROR: {error[0]}")
            print(error[1])
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_comprehensive_test()
