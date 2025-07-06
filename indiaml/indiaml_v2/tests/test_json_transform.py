import unittest
import sqlite3
import tempfile
import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Import our pipeline classes
from indiaml_v2.pipeline.paper_pipeline import (
    PipelineConfig, StatusNormalizer, CountryCodeMapper, 
    SortingCalculator, PaperDataPipeline
)

class TestDatabase:
    """Helper class to create test database with sample data"""
    
    @staticmethod
    def create_test_db(db_path: str):
        """Create a test database with sample data"""
        conn = sqlite3.connect(db_path)
        
        # Create tables (simplified schema for testing)
        conn.execute("""
        CREATE TABLE countries (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT
        )
        """)
        
        conn.execute("""
        CREATE TABLE institutions (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            country_id INTEGER,
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
        """)
        
        conn.execute("""
        CREATE TABLE authors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            name_site TEXT,
            openreview_id TEXT,
            gender TEXT,
            homepage_url TEXT,
            dblp_id TEXT,
            google_scholar_url TEXT,
            orcid TEXT,
            linkedin_url TEXT,
            twitter_url TEXT,
            primary_email TEXT
        )
        """)
        
        conn.execute("""
        CREATE TABLE affiliations (
            id INTEGER PRIMARY KEY,
            author_id TEXT,
            institution_id INTEGER,
            is_primary BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (author_id) REFERENCES authors(id),
            FOREIGN KEY (institution_id) REFERENCES institutions(id)
        )
        """)
        
        conn.execute("""
        CREATE TABLE conferences (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            year INTEGER NOT NULL
        )
        """)
        
        conn.execute("""
        CREATE TABLE tracks (
            id INTEGER PRIMARY KEY,
            conference_id INTEGER,
            name TEXT NOT NULL,
            FOREIGN KEY (conference_id) REFERENCES conferences(id)
        )
        """)
        
        conn.execute("""
        CREATE TABLE papers (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT,
            track_id INTEGER,
            abstract TEXT,
            tldr TEXT,
            site_url TEXT,
            pdf_url TEXT,
            github_url TEXT,
            author_count INTEGER,
            FOREIGN KEY (track_id) REFERENCES tracks(id)
        )
        """)
        
        conn.execute("""
        CREATE TABLE paper_authors (
            id INTEGER PRIMARY KEY,
            paper_id TEXT,
            author_id TEXT,
            author_order INTEGER,
            FOREIGN KEY (paper_id) REFERENCES papers(id),
            FOREIGN KEY (author_id) REFERENCES authors(id)
        )
        """)
        
        conn.execute("""
        CREATE TABLE paper_author_affiliations (
            id INTEGER PRIMARY KEY,
            paper_author_id INTEGER,
            affiliation_id INTEGER,
            is_primary BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (paper_author_id) REFERENCES paper_authors(id),
            FOREIGN KEY (affiliation_id) REFERENCES affiliations(id)
        )
        """)
        
        conn.execute("""
        CREATE TABLE review_statistics (
            id INTEGER PRIMARY KEY,
            paper_id TEXT UNIQUE,
            rating_mean REAL,
            rating_std REAL,
            confidence_mean REAL,
            confidence_std REAL,
            total_reviews INTEGER,
            total_reviewers INTEGER,
            FOREIGN KEY (paper_id) REFERENCES papers(id)
        )
        """)
        
        conn.execute("""
        CREATE TABLE citations (
            id INTEGER PRIMARY KEY,
            paper_id TEXT UNIQUE,
            google_scholar_citations INTEGER DEFAULT 0,
            semantic_scholar_citations INTEGER,
            FOREIGN KEY (paper_id) REFERENCES papers(id)
        )
        """)
        
        # Insert sample data
        TestDatabase._insert_sample_data(conn)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def _insert_sample_data(conn):
        """Insert sample test data"""
        # Countries
        countries_data = [
            (1, 'United States', 'US'),
            (2, 'China', 'CN'),
            (3, 'United Kingdom', 'GB'),
            (4, 'Germany', 'DE'),
            (5, 'Invalid Country Name!@#$', None)  # Adversarial case
        ]
        conn.executemany("INSERT INTO countries VALUES (?, ?, ?)", countries_data)
        
        # Institutions
        institutions_data = [
            (1, 'Stanford University', 'stanford university', 1),
            (2, 'MIT', 'massachusetts institute of technology', 1),
            (3, 'Tsinghua University', 'tsinghua university', 2),
            (4, 'University of Cambridge', 'university of cambridge', 3),
            (5, 'Max Planck Institute', 'max planck institute', 4),
            (6, 'Unknown Institute', 'unknown institute', 5)  # Adversarial case
        ]
        conn.executemany("INSERT INTO institutions VALUES (?, ?, ?, ?)", institutions_data)
        
        # Authors
        authors_data = [
            ('author1', 'John Doe', 'John Doe Site', 'openreview123', 'M', 'http://johndoe.com', 'dblp:john-doe', 'http://scholar.google.com/johndoe', '0000-0000-0000-0001', 'http://linkedin.com/in/johndoe', 'http://twitter.com/johndoe', 'john@stanford.edu'),
            ('author2', 'Jane Smith', 'Jane Smith', 'openreview456', 'F', None, None, None, '0000-0000-0000-0002', 'http://linkedin.com/in/janesmith', None, 'jane@stanford.edu'),
            ('author3', 'Bob Johnson', '', '', 'M', '', '', '', '', '', '', ''),  # Empty strings
            ('author4', 'Alice Brown', 'Alice Brown', 'openreview789', 'F', 'http://alice.com', 'dblp:alice-brown', 'http://scholar.google.com/alice', '0000-0000-0000-0003', 'http://linkedin.com/in/alicebrown', 'http://twitter.com/alicebrown', 'alice@cambridge.ac.uk'),
            ('author5', 'Charlie Wilson', 'Charlie Wilson', None, 'Unspecified', None, None, None, None, None, None, 'charlie@mpi.de'),
            ('', 'Empty ID Author', '', '', 'M', None, None, None, None, None, None, None),  # Adversarial: empty ID
            ('author_chinese', '张三', '张三', 'openreview_chinese', 'M', None, None, None, None, None, None, 'zhang@stanford.edu'),  # Unicode name
            ('author_special', "Name with 'quotes' and \"double quotes\"", "Name with 'quotes'", 'openreview_special', 'F', None, None, None, None, None, None, None)  # Special characters
        ]
        conn.executemany("INSERT INTO authors VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", authors_data)
        
        # Affiliations
        affiliations_data = [
            (1, 'author1', 1, True),   # John at Stanford (primary)
            (2, 'author1', 2, False),  # John also at MIT
            (3, 'author2', 1, True),   # Jane at Stanford
            (4, 'author3', 3, True),   # Bob at Tsinghua
            (5, 'author4', 4, True),   # Alice at Cambridge
            (6, 'author5', 5, True),   # Charlie at Max Planck
            (7, '', 6, True),          # Adversarial: empty author ID
            (8, 'author_chinese', 1, True),  # Chinese author at Stanford
        ]
        conn.executemany("INSERT INTO affiliations VALUES (?, ?, ?, ?)", affiliations_data)
        
        # Conferences
        conferences_data = [
            (1, 'ICML', 2024),
            (2, 'NeurIPS', 2024),
            (3, 'ICLR', 2024),
            (4, 'Conference with Weird Name!@#$', 2024)  # Adversarial
        ]
        conn.executemany("INSERT INTO conferences VALUES (?, ?, ?)", conferences_data)
        
        # Tracks
        tracks_data = [
            (1, 1, 'Main Conference'),
            (2, 2, 'Main Conference'),
            (3, 3, 'Main Conference'),
            (4, 4, 'Workshop Track'),
        ]
        conn.executemany("INSERT INTO tracks VALUES (?, ?, ?)", tracks_data)
        
        # Papers with various status types
        papers_data = [
            ('paper1', 'Deep Learning Paper', 'Oral', 1, 'Abstract 1', 'TLDR 1', 'http://site1.com', 'http://pdf1.com', 'http://github1.com', 3),
            ('paper2', 'Machine Learning Paper', 'Spotlight', 1, 'Abstract 2', 'TLDR 2', 'http://site2.com', None, None, 2),
            ('paper3', 'AI Paper', 'Poster', 2, 'Abstract 3', 'TLDR 3', None, 'http://pdf3.com', 'http://github3.com', 4),
            ('paper4', 'Rejected Paper', 'Reject', 2, 'Abstract 4', 'TLDR 4', None, None, None, 1),
            ('paper5', 'Workshop Paper', 'Oral Workshop', 3, 'Abstract 5', None, 'http://site5.com', 'http://pdf5.com', None, 2),
            ('paper6', 'Top Paper', 'Top-5%', 3, 'Abstract 6', 'TLDR 6', 'http://site6.com', 'http://pdf6.com', 'http://github6.com', 3),
            ('paper7', 'Unknown Status Paper', 'Some Random Status', 1, 'Abstract 7', 'TLDR 7', None, None, None, 1),
            ('', 'Paper with Empty ID', 'Poster', 1, '', '', '', '', '', 0),  # Adversarial cases
            ('paper_unicode', 'Paper with Unicode: 深度学习', 'Oral', 1, 'Unicode abstract: 这是一个摘要', 'Unicode TLDR', None, None, None, 1),
        ]
        conn.executemany("INSERT INTO papers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", papers_data)
        
        # Paper-Author relationships
        paper_authors_data = [
            (1, 'paper1', 'author1', 1),    # John is first author
            (2, 'paper1', 'author2', 2),    # Jane is second author
            (3, 'paper1', 'author4', 3),    # Alice is third author
            (4, 'paper2', 'author2', 1),    # Jane is first author
            (5, 'paper2', 'author3', 2),    # Bob is second author
            (6, 'paper3', 'author3', 1),    # Bob is first author
            (7, 'paper3', 'author1', 2),    # John is second author
            (8, 'paper3', 'author4', 3),    # Alice is third author
            (9, 'paper3', 'author5', 4),    # Charlie is fourth author
            (10, 'paper4', 'author5', 1),   # Charlie is sole author
            (11, 'paper5', 'author_chinese', 1),  # Chinese author first
            (12, 'paper5', 'author1', 2),   # John second
            (13, 'paper6', 'author1', 1),   # John first
            (14, 'paper6', 'author2', 2),   # Jane second
            (15, 'paper6', 'author4', 3),   # Alice third (last author effect)
            (16, 'paper7', 'author2', 1),   # Jane sole author
            (17, '', 'author1', 1),         # Adversarial: empty paper ID
            (18, 'paper_unicode', 'author_chinese', 1),  # Unicode paper
        ]
        conn.executemany("INSERT INTO paper_authors VALUES (?, ?, ?, ?)", paper_authors_data)
        
        # Paper-Author-Affiliations
        paa_data = [
            (1, 1, 1, True),   # paper1, author1, Stanford
            (2, 2, 3, True),   # paper1, author2, Stanford  
            (3, 3, 5, True),   # paper1, author4, Cambridge
            (4, 4, 3, True),   # paper2, author2, Stanford
            (5, 5, 4, True),   # paper2, author3, Tsinghua
            # Add more as needed...
        ]
        conn.executemany("INSERT INTO paper_author_affiliations VALUES (?, ?, ?, ?)", paa_data)
        
        # Review statistics
        review_stats_data = [
            (1, 'paper1', 8.5, 0.5, 4.2, 0.3, 3, 3),
            (2, 'paper2', 7.0, 1.0, 3.8, 0.6, 3, 3),
            (3, 'paper3', 6.5, 1.2, 3.5, 0.8, 4, 4),
            (4, 'paper5', 7.8, 0.7, 4.0, 0.4, 2, 2),
            (5, 'paper6', 9.0, 0.3, 4.5, 0.2, 3, 3),
        ]
        conn.executemany("INSERT INTO review_statistics VALUES (?, ?, ?, ?, ?, ?, ?, ?)", review_stats_data)
        
        # Citations
        citations_data = [
            (1, 'paper1', 150, 140),
            (2, 'paper2', 80, 75),
            (3, 'paper3', 45, 42),
            (4, 'paper5', 25, 20),
            (5, 'paper6', 200, 185),
        ]
        conn.executemany("INSERT INTO citations VALUES (?, ?, ?, ?)", citations_data)

class TestStatusNormalizer(unittest.TestCase):
    """Test cases for status normalization"""
    
    def test_standard_statuses(self):
        """Test normalization of standard status values"""
        test_cases = [
            ('Oral', 'oral'),
            ('Spotlight', 'spotlight'),
            ('Poster', 'poster'),
            ('Reject', 'rejected'),
            ('Withdraw', 'withdrawn'),
        ]
        
        for input_status, expected in test_cases:
            with self.subTest(input_status=input_status):
                self.assertEqual(StatusNormalizer.normalize_status(input_status), expected)
    
    def test_case_insensitive(self):
        """Test case insensitive normalization"""
        test_cases = [
            ('ORAL', 'oral'),
            ('oral', 'oral'),
            ('Oral', 'oral'),
            ('oRaL', 'oral'),
        ]
        
        for input_status, expected in test_cases:
            with self.subTest(input_status=input_status):
                self.assertEqual(StatusNormalizer.normalize_status(input_status), expected)
    
    def test_workshop_variants(self):
        """Test workshop status variants"""
        test_cases = [
            ('Oral Workshop', 'oral'),
            ('Poster Workshop', 'poster'),
            ('oral workshop', 'oral'),
            ('POSTER WORKSHOP', 'poster'),
        ]
        
        for input_status, expected in test_cases:
            with self.subTest(input_status=input_status):
                self.assertEqual(StatusNormalizer.normalize_status(input_status), expected)
    
    def test_adversarial_cases(self):
        """Test adversarial and edge cases"""
        test_cases = [
            (None, 'unknown'),
            ('', 'unknown'),
            ('   ', 'unknown'),
            ('Random Status', 'unknown'),
            ('Oral123', 'unknown'),
            ('Not a real status!@#$', 'unknown'),
            ('Top-5%', 'oral'),
            ('Top-25%', 'spotlight'),
        ]
        
        for input_status, expected in test_cases:
            with self.subTest(input_status=input_status):
                self.assertEqual(StatusNormalizer.normalize_status(input_status), expected)

class TestCountryCodeMapper(unittest.TestCase):
    """Test cases for country code mapping"""
    
    def test_standard_countries(self):
        """Test standard country mappings"""
        test_cases = [
            ('United States', 'US'),
            ('China', 'CN'),
            ('United Kingdom', 'GB'),
            ('Germany', 'DE'),
        ]
        
        for country, expected_code in test_cases:
            with self.subTest(country=country):
                self.assertEqual(CountryCodeMapper.get_country_code(country), expected_code)
    
    def test_case_insensitive(self):
        """Test case insensitive mapping"""
        test_cases = [
            ('UNITED STATES', 'US'),
            ('united states', 'US'),
            ('United States', 'US'),
            ('uNiTeD sTaTeS', 'US'),
        ]
        
        for country, expected_code in test_cases:
            with self.subTest(country=country):
                self.assertEqual(CountryCodeMapper.get_country_code(country), expected_code)
    
    def test_country_variants(self):
        """Test country name variants"""
        test_cases = [
            ('USA', 'US'),
            ('United States of America', 'US'),
            ('UK', 'GB'),
            ('Korea', 'KR'),
            ('South Korea', 'KR'),
        ]
        
        for country, expected_code in test_cases:
            with self.subTest(country=country):
                self.assertEqual(CountryCodeMapper.get_country_code(country), expected_code)
    
    def test_adversarial_cases(self):
        """Test adversarial cases"""
        test_cases = [
            (None, 'UN'),
            ('', 'UN'),
            ('   ', 'UN'),
            ('Unknown Country', 'UN'),
            ('Country!@#$', 'UN'),
            ('123', 'UN'),
        ]
        
        for country, expected_code in test_cases:
            with self.subTest(country=country):
                self.assertEqual(CountryCodeMapper.get_country_code(country), expected_code)

class TestSortingCalculator(unittest.TestCase):
    """Test cases for sorting score calculation"""
    
    def setUp(self):
        self.config = PipelineConfig()
        self.calculator = SortingCalculator(self.config)
    
    def test_author_position_weights(self):
        """Test author position weight calculation"""
        # Single author paper
        self.assertEqual(
            self.calculator.calculate_author_position_weight(1, 1),
            self.config.first_author_weight
        )
        
        # Multi-author paper
        self.assertEqual(
            self.calculator.calculate_author_position_weight(1, 3),
            self.config.first_author_weight
        )
        
        self.assertEqual(
            self.calculator.calculate_author_position_weight(3, 3),
            self.config.last_author_weight
        )
        
        # Middle author should get reduced weight
        middle_weight = self.calculator.calculate_author_position_weight(2, 3)
        self.assertLess(middle_weight, self.config.first_author_weight)
        self.assertLess(middle_weight, self.config.last_author_weight)
    
    def test_paper_score_calculation(self):
        """Test overall paper score calculation"""
        # Oral first author should get highest score
        oral_first = self.calculator.calculate_paper_score('Oral', 1, 3)
        
        # Poster first author should get lower score
        poster_first = self.calculator.calculate_paper_score('Poster', 1, 3)
        
        # Oral last author
        oral_last = self.calculator.calculate_paper_score('Oral', 3, 3)
        
        self.assertGreater(oral_first, poster_first)
        self.assertGreater(oral_first, oral_last)
        self.assertGreater(oral_last, poster_first)
    
    def test_rejected_papers(self):
        """Test that rejected papers get zero score"""
        rejected_score = self.calculator.calculate_paper_score('Reject', 1, 1)
        withdrawn_score = self.calculator.calculate_paper_score('Withdraw', 1, 1)
        
        self.assertEqual(rejected_score, 0.0)
        self.assertEqual(withdrawn_score, 0.0)
    
    def test_graceful_error_handling(self):
        """Test that invalid inputs are handled gracefully without crashing"""
        # These should all return 0.0 instead of crashing
        test_cases = [
            ('Oral', 0, 3),      # Invalid position (0)
            ('Oral', -1, 3),     # Invalid position (negative)
            ('Oral', 1, 0),      # Invalid total authors (0)
            ('Oral', 1, -1),     # Invalid total authors (negative)
            ('Oral', 5, 3),      # Position > total authors
            ('Poster', 10, 2),   # Way out of range
        ]
        
        for status, position, total in test_cases:
            with self.subTest(status=status, position=position, total=total):
                score = self.calculator.calculate_paper_score(status, position, total)
                self.assertEqual(score, 0.0, 
                    f"Expected 0.0 for invalid inputs ({status}, {position}, {total}), got {score}")
    
    def test_adversarial_inputs(self):
        """Test adversarial inputs"""
        # Zero authors (shouldn't happen but test anyway)
        with self.assertRaises(ValueError):
            self.calculator.calculate_author_position_weight(1, 0)
        
        # Negative total authors
        with self.assertRaises(ValueError):
            self.calculator.calculate_author_position_weight(1, -1)
        
        # Invalid author position (zero)
        with self.assertRaises(ValueError):
            self.calculator.calculate_author_position_weight(0, 3)
        
        # Invalid author position (negative)
        with self.assertRaises(ValueError):
            self.calculator.calculate_author_position_weight(-1, 3)
        
        # Position greater than total authors
        with self.assertRaises(ValueError):
            self.calculator.calculate_author_position_weight(5, 3)
        
        # Test with unknown status (should not crash)
        weird_score = self.calculator.calculate_paper_score('Unknown Status', 1, 3)
        self.assertIsInstance(weird_score, float)
        self.assertGreater(weird_score, 0)  # Should get some positive score
        
        # Test that calculate_paper_score handles invalid inputs gracefully
        invalid_score1 = self.calculator.calculate_paper_score('Oral', -1, 3)
        self.assertEqual(invalid_score1, 0.0)  # Should return 0 for invalid inputs
        
        invalid_score2 = self.calculator.calculate_paper_score('Oral', 1, 0)
        self.assertEqual(invalid_score2, 0.0)  # Should return 0 for invalid inputs
        
        invalid_score3 = self.calculator.calculate_paper_score('Oral', 5, 3)
        self.assertEqual(invalid_score3, 0.0)  # Should return 0 for invalid inputs

class TestPaperDataPipeline(unittest.TestCase):
    """Integration tests for the main pipeline"""
    
    def setUp(self):
        """Set up test database and pipeline"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test.db')
        TestDatabase.create_test_db(self.db_path)
        
        self.config = PipelineConfig()
        self.pipeline = PaperDataPipeline(self.db_path, self.config)
    
    def tearDown(self):
        """Clean up test files"""
        shutil.rmtree(self.test_dir)
    
    def test_get_focus_country_authors(self):
        """Test getting authors from focus country"""
        # Test with valid country
        us_authors = self.pipeline.get_focus_country_authors('United States')
        self.assertIn('author1', us_authors)  # John at Stanford
        self.assertIn('author2', us_authors)  # Jane at Stanford
        self.assertIn('author_chinese', us_authors)  # Chinese author at Stanford
        
        # Test with different country
        china_authors = self.pipeline.get_focus_country_authors('China')
        self.assertIn('author3', china_authors)  # Bob at Tsinghua
        
        # Test with non-existent country
        fake_authors = self.pipeline.get_focus_country_authors('Non-existent Country')
        self.assertEqual(len(fake_authors), 0)
    
    def test_get_papers_by_conference(self):
        """Test getting papers organized by conference"""
        us_authors = self.pipeline.get_focus_country_authors('United States')
        papers_by_conf = self.pipeline.get_papers_by_conference(us_authors)
        
        self.assertGreater(len(papers_by_conf), 0)
        
        # Check that papers are properly structured
        for conf_name, papers in papers_by_conf.items():
            self.assertIsInstance(papers, list)
            for paper in papers:
                self.assertIn('paper_id', paper)
                self.assertIn('title', paper)
                self.assertIn('status', paper)
                self.assertIn('normalized_status', paper)
                self.assertIn('sort_score', paper)
                self.assertIn('author', paper)
    
    def test_author_attributes_included(self):
        """Test that all author attributes from the model are included in the output"""
        us_authors = self.pipeline.get_focus_country_authors('United States')
        papers_by_conf = self.pipeline.get_papers_by_conference(us_authors)
        
        # Find a paper with author1 (John Doe) who has complete profile data
        found_complete_author = False
        for conf_name, papers in papers_by_conf.items():
            for paper in papers:
                if paper['author']['id'] == 'author1':
                    author = paper['author']
                    
                    # Check that all the new attributes are present
                    expected_attributes = [
                        'id', 'name', 'name_site', 'openreview_id', 'position', 'gender',
                        'homepage_url', 'dblp_id', 'google_scholar_url', 'orcid', 
                        'linkedin_url', 'twitter_url', 'primary_email', 'affiliations',
                        'countries', 'country_codes'
                    ]
                    
                    for attr in expected_attributes:
                        self.assertIn(attr, author, f"Missing attribute: {attr}")
                    
                    # Check specific values for author1
                    self.assertEqual(author['name'], 'John Doe')
                    self.assertEqual(author['name_site'], 'John Doe Site')
                    self.assertEqual(author['openreview_id'], 'openreview123')
                    self.assertEqual(author['dblp_id'], 'dblp:john-doe')
                    self.assertEqual(author['orcid'], '0000-0000-0000-0001')
                    self.assertEqual(author['linkedin_url'], 'http://linkedin.com/in/johndoe')
                    self.assertEqual(author['twitter_url'], 'http://twitter.com/johndoe')
                    self.assertEqual(author['primary_email'], 'john@stanford.edu')
                    
                    found_complete_author = True
                    break
            if found_complete_author:
                break
        
        self.assertTrue(found_complete_author, "Could not find author1 with complete profile data")
        
        # Also test that None/empty values are handled properly
        found_minimal_author = False
        for conf_name, papers in papers_by_conf.items():
            for paper in papers:
                if paper['author']['id'] == 'author2':
                    author = paper['author']
                    
                    # author2 has some None values, check they're handled properly
                    self.assertEqual(author['name'], 'Jane Smith')
                    self.assertEqual(author['orcid'], '0000-0000-0000-0002')
                    self.assertIsNone(author['homepage_url'])
                    self.assertIsNone(author['dblp_id'])
                    self.assertIsNone(author['twitter_url'])
                    
                    found_minimal_author = True
                    break
            if found_minimal_author:
                break
        
        self.assertTrue(found_minimal_author, "Could not find author2 with minimal profile data")
    
    def test_get_review_data(self):
        """Test getting review statistics"""
        paper_ids = ['paper1', 'paper2', 'paper3']
        review_data = self.pipeline.get_review_data(paper_ids)
        
        self.assertIn('paper1', review_data)
        self.assertIn('rating_mean', review_data['paper1'])
        self.assertIn('total_reviews', review_data['paper1'])
    
    def test_process_and_export_json(self):
        """Test full pipeline with JSON output"""
        output_dir = os.path.join(self.test_dir, 'output')
        
        output_files = self.pipeline.process_and_export('United States', output_dir)
        
        self.assertGreater(len(output_files), 0)
        
        # Check that files were created
        for conf_name, filepath in output_files.items():
            self.assertTrue(os.path.exists(filepath))
            
            # Check JSON structure
            with open(filepath, 'r') as f:
                data = json.load(f)
                self.assertIn('conference', data)
                self.assertIn('focus_country', data)
                self.assertIn('papers', data)
                self.assertIn('config', data)
    
    def test_process_and_export_csv(self):
        """Test full pipeline with CSV output"""
        self.config.output_format = 'csv'
        self.pipeline.config = self.config
        
        output_dir = os.path.join(self.test_dir, 'output_csv')
        
        output_files = self.pipeline.process_and_export('United States', output_dir)
        
        # Check that CSV files were created and are readable
        for conf_name, filepath in output_files.items():
            self.assertTrue(os.path.exists(filepath))
            df = pd.read_csv(filepath)
            self.assertGreater(len(df), 0)
            self.assertIn('paper_id', df.columns)
            self.assertIn('sort_score', df.columns)
    
    def test_adversarial_database_conditions(self):
        """Test pipeline with adversarial database conditions"""
        # Test with non-existent database
        fake_pipeline = PaperDataPipeline('/non/existent/path.db', self.config)
        
        with self.assertRaises(Exception):
            fake_pipeline.get_focus_country_authors('United States')
        
        # Test with empty results
        empty_authors = self.pipeline.get_focus_country_authors('Mars')
        self.assertEqual(len(empty_authors), 0)
        
        papers_empty = self.pipeline.get_papers_by_conference([])
        self.assertEqual(len(papers_empty), 0)
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters"""
        # This should work without errors
        papers = self.pipeline.get_papers_by_conference(['author_chinese'])
        
        # Should find the Unicode paper
        found_unicode = False
        for conf_papers in papers.values():
            for paper in conf_papers:
                if 'Unicode' in paper['title'] or '深度学习' in paper['title']:
                    found_unicode = True
                    break
        
        self.assertTrue(found_unicode)
    
    def test_empty_and_none_values(self):
        """Test handling of empty and None values"""
        # The pipeline should handle empty/None values gracefully
        # This is tested implicitly through the sample data which includes empty strings and None values
        
        us_authors = self.pipeline.get_focus_country_authors('United States')
        papers_by_conf = self.pipeline.get_papers_by_conference(us_authors)
        
        # Should complete without errors despite having empty/None values in the test data
        self.assertIsInstance(papers_by_conf, dict)
    
    def test_sorting_consistency(self):
        """Test that sorting produces consistent and logical results"""
        us_authors = self.pipeline.get_focus_country_authors('United States')
        papers_by_conf = self.pipeline.get_papers_by_conference(us_authors)
        
        for conf_name, papers in papers_by_conf.items():
            # Sort papers by score
            sorted_papers = sorted(papers, key=lambda x: x['sort_score'], reverse=True)
            
            # Check that oral papers generally rank higher than poster papers
            # (when same author position)
            oral_papers = [p for p in sorted_papers if p['normalized_status'] == 'oral']
            poster_papers = [p for p in sorted_papers if p['normalized_status'] == 'poster']
            
            if oral_papers and poster_papers:
                # Find first authors
                oral_first_authors = [p for p in oral_papers if p['author']['position'] == 1]
                poster_first_authors = [p for p in poster_papers if p['author']['position'] == 1]
                
                if oral_first_authors and poster_first_authors:
                    max_oral_score = max(p['sort_score'] for p in oral_first_authors)
                    max_poster_score = max(p['sort_score'] for p in poster_first_authors)
                    self.assertGreater(max_oral_score, max_poster_score)

class TestPipelineConfig(unittest.TestCase):
    """Test cases for pipeline configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = PipelineConfig()
        
        self.assertEqual(config.first_author_weight, 3.0)
        self.assertEqual(config.last_author_weight, 2.0)
        self.assertEqual(config.middle_author_weight, 1.0)
        self.assertIn('oral', config.status_weights)
        self.assertEqual(config.output_format, 'json')
    
    def test_custom_config(self):
        """Test custom configuration"""
        custom_weights = {
            'oral': 20.0,
            'spotlight': 15.0,
            'poster': 8.0,
            'unknown': 1.0
        }
        
        config = PipelineConfig(
            first_author_weight=5.0,
            status_weights=custom_weights,
            output_format='csv'
        )
        
        self.assertEqual(config.first_author_weight, 5.0)
        self.assertEqual(config.status_weights['oral'], 20.0)
        self.assertEqual(config.output_format, 'csv')

class TestEdgeCasesAndPerformance(unittest.TestCase):
    """Test edge cases and performance scenarios"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test.db')
        TestDatabase.create_test_db(self.db_path)
        self.pipeline = PaperDataPipeline(self.db_path)
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_large_author_list(self):
        """Test pipeline with large list of authors"""
        # Create a large list of author IDs (some valid, some invalid)
        large_author_list = [f'author{i}' for i in range(1000)]
        large_author_list.extend(['author1', 'author2', 'author3'])  # Add some valid ones
        
        # This should not crash and should handle the large list efficiently
        papers = self.pipeline.get_papers_by_conference(large_author_list)
        self.assertIsInstance(papers, dict)
    
    def test_special_characters_in_filenames(self):
        """Test handling of special characters in conference names for file output"""
        # The test database includes a conference with special characters
        output_dir = os.path.join(self.test_dir, 'special_output')
        
        # This should not crash despite special characters in conference names
        try:
            output_files = self.pipeline.process_and_export('Invalid Country Name!@#$', output_dir)
            # Even if no papers found, it should not crash
            self.assertIsInstance(output_files, dict)
        except ValueError as e:
            # This is expected if no authors found
            self.assertIn('No authors found', str(e))
    
    def test_malformed_database_queries(self):
        """Test handling of malformed or problematic database queries"""
        # Test with SQL injection attempt (should be safe due to parameterized queries)
        malicious_country = "'; DROP TABLE authors; --"
        
        # This should return empty results, not crash
        authors = self.pipeline.get_focus_country_authors(malicious_country)
        self.assertEqual(len(authors), 0)

if __name__ == '__main__':
    # Create a test suite that runs all tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestStatusNormalizer,
        TestCountryCodeMapper,
        TestSortingCalculator,
        TestPaperDataPipeline,
        TestPipelineConfig,
        TestEdgeCasesAndPerformance
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors))/result.testsRun*100:.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
