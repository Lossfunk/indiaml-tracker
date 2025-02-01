import unittest
from datetime import datetime
from typing import List, Dict, Any
from indiaml.pipeline.affiliation_checker import AffiliationChecker


class TestAffiliationChecker(unittest.TestCase):
    def setUp(self):
        self.affiliation_checker = AffiliationChecker()

    def test_no_affiliation_history(self):
        # Test with empty affiliation history
        affiliation_history = []
        paper_date = datetime(2023, 6, 15)
        result = self.affiliation_checker.resolve_affiliation(affiliation_history, paper_date)
        self.assertIsNone(result)

    def test_single_affiliation_within_date(self):
        # Test a single affiliation that covers the paper date
        affiliation_history = [
            {
                "position": "Researcher",
                "start": 2020,
                "end": 2025,
                "institution": {
                    "domain": "mit.edu",
                    "name": "Massachusetts Institute of Technology",
                    "country": "USA"
                }
            }
        ]
        paper_date = datetime(2023, 3, 10)
        expected = {
            'name': "Massachusetts Institute of Technology",
            'domain': "mit.edu",
            'country': "USA"
        }
        result = self.affiliation_checker.resolve_affiliation(affiliation_history, paper_date)
        self.assertEqual(result, expected)

    def test_single_affiliation_outside_date(self):
        # Test a single affiliation that does not cover the paper date
        affiliation_history = [
            {
                "position": "Undergrad student",
                "start": 2014,
                "end": 2018,
                "institution": {
                    "domain": "tju.edu",
                    "name": "Tianjin University",
                    "country": "CHN"
                }
            }
        ]
        paper_date = datetime(2019, 1, 1)
        result = self.affiliation_checker.resolve_affiliation(affiliation_history, paper_date)
        self.assertIsNone(result)

    def test_multiple_affiliations_no_overlap(self):
        # Test multiple non-overlapping affiliations
        affiliation_history = [
            {
                "position": "Undergrad student",
                "start": 2014,
                "end": 2018,
                "institution": {
                    "domain": "tju.edu",
                    "name": "Tianjin University",
                    "country": "CHN"
                }
            },
            {
                "position": "MS student",
                "start": 2019,
                "end": 2021,
                "institution": {
                    "domain": "usc.edu",
                    "name": "University of Southern California",
                    "country": "USA"
                }
            },
            {
                "position": "PhD student",
                "start": 2021,
                "end": 2022,
                "institution": {
                    "domain": "scu.edu",
                    "name": "Santa Clara University",
                    "country": "USA"
                }
            },
            {
                "position": "PhD student",
                "start": 2022,
                "end": 2027,
                "institution": {
                    "domain": "rit.edu",
                    "name": "Rochester Institute of Technology",
                    "country": "US"
                }
            }
        ]
        # Test a date within the second affiliation
        paper_date = datetime(2020, 5, 20)
        expected = {
            'name': "University of Southern California",
            'domain': "usc.edu",
            'country': "USA"
        }
        result = self.affiliation_checker.resolve_affiliation(affiliation_history, paper_date)
        self.assertEqual(result, expected)

        # Test a date within the last affiliation
        paper_date = datetime(2023, 6, 15)
        expected = {
            'name': "Rochester Institute of Technology",
            'domain': "rit.edu",
            'country': "US"
        }
        result = self.affiliation_checker.resolve_affiliation(affiliation_history, paper_date)
        self.assertEqual(result, expected)

    def test_multiple_affiliations_with_overlap(self):
        # Test multiple affiliations with overlapping periods
        affiliation_history = [
            {
                "position": "Researcher",
                "start": 2020,
                "end": 2025,
                "institution": {
                    "domain": "mit.edu",
                    "name": "Massachusetts Institute of Technology",
                    "country": "USA"
                }
            },
            {
                "position": "Visiting Scholar",
                "start": 2023,
                "end": 2024,
                "institution": {
                    "domain": "stanford.edu",
                    "name": "Stanford University",
                    "country": "USA"
                }
            }
        ]
        # Assuming the first matching record is returned
        paper_date = datetime(2023, 6, 15)
        expected = {
            'name': "Massachusetts Institute of Technology",
            'domain': "mit.edu",
            'country': "USA"
        }
        result = self.affiliation_checker.resolve_affiliation(affiliation_history, paper_date)
        self.assertEqual(result, expected)

    def test_affiliation_with_no_country(self):
        # Test affiliation records missing the 'country' field
        affiliation_history = [
            {
                "position": "Researcher",
                "start": 2021,
                "end": 2023,
                "institution": {
                    "domain": "unknown.edu",
                    "name": "Unknown University"
                    # 'country' is missing
                }
            }
        ]
        paper_date = datetime(2022, 7, 1)
        expected = {
            'name': "Unknown University",
            'domain': "unknown.edu",
            'country': "UNK"  # Default value
        }
        result = self.affiliation_checker.resolve_affiliation(affiliation_history, paper_date)
        self.assertEqual(result, expected)

    def test_invalid_dates_in_affiliation_history(self):
        # Test affiliation records with invalid date formats
        affiliation_history = [
            {
                "position": "Researcher",
                "start": "2020",  # Should be an integer
                "end": "invalid_end",  # Invalid
                "institution": {
                    "domain": "mit.edu",
                    "name": "Massachusetts Institute of Technology",
                    "country": "USA"
                }
            }
        ]
        paper_date = datetime(2021, 1, 1)
        # Expecting no affiliation due to invalid dates
        result = self.affiliation_checker.resolve_affiliation(affiliation_history, paper_date)
        self.assertIsNone(result)

    def test_partial_affiliation_records(self):
        # Test affiliation records with missing fields
        affiliation_history = [
            {
                "position": "Researcher",
                "start": 2020,
                # 'end' is missing
                "institution": {
                    "domain": "mit.edu",
                    "name": "Massachusetts Institute of Technology",
                    "country": "USA"
                }
            },
            {
                "position": "Visiting Scholar",
                "end": 2022,
                # 'start' is missing
                "institution": {
                    "domain": "stanford.edu",
                    "name": "Stanford University",
                    "country": "USA"
                }
            }
        ]
        # Test a date after the first affiliation starts
        paper_date = datetime(2021, 6, 15)
        expected = {
            'name': "Massachusetts Institute of Technology",
            'domain': "mit.edu",
            'country': "USA"
        }
        result = self.affiliation_checker.resolve_affiliation(affiliation_history, paper_date)
        self.assertEqual(result, expected)

        # Test a date before the first affiliation ends but no start date in the second
        paper_date = datetime(2022, 5, 10)
        expected = {
            'name': "Massachusetts Institute of Technology",
            'domain': "mit.edu",
            'country': "USA"
        }
        result = self.affiliation_checker.resolve_affiliation(affiliation_history, paper_date)
        self.assertEqual(result, expected)

        # Test a date after the second affiliation's end date
        paper_date = datetime(2023, 1, 1)
        expected = {
            'name': "Massachusetts Institute of Technology",
            'domain': "mit.edu",
            'country': "USA"
        }
        result = self.affiliation_checker.resolve_affiliation(affiliation_history, paper_date)
        self.assertEqual(result, expected)

    def test_affiliation_record_with_none_values(self):
        # Test affiliation records with None values
        affiliation_history = [
            {
                "position": "Researcher",
                "start": None,
                "end": None,
                "institution": {
                    "domain": "global.edu",
                    "name": "Global University",
                    "country": "GBR"
                }
            }
        ]
        paper_date = datetime(2022, 8, 20)
        expected = {
            'name': "Global University",
            'domain': "global.edu",
            'country': "GBR"
        }
        result = self.affiliation_checker.resolve_affiliation(affiliation_history, paper_date)
        self.assertEqual(result, expected)

    
if __name__ == '__main__':
    unittest.main()
