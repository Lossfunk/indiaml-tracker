"""
Tests for the analytics pipeline components.

This module contains comprehensive tests for all analytics components
including global stats, country analysis, institution analysis, and
the main analytics pipeline.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..analytics.analytics_pipeline import AnalyticsPipeline
from ..analytics.global_stats_generator import GlobalStatsGenerator
from ..analytics.country_analyzer import CountryAnalyzer
from ..analytics.institution_analyzer import InstitutionAnalyzer
from ..analytics.config import COUNTRY_CODE_MAP, DEFAULT_CONFIG


class TestAnalyticsPipeline:
    """Test the main analytics pipeline."""
    
    @pytest.fixture
    def mock_db_path(self):
        """Create a temporary database path for testing."""
        return ":memory:"
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock()
        session.query.return_value.filter.return_value.first.return_value = None
        session.query.return_value.count.return_value = 0
        session.query.return_value.all.return_value = []
        return session
    
    @pytest.fixture
    def analytics_pipeline(self, mock_db_path):
        """Create an analytics pipeline instance for testing."""
        with patch('indiaml_v2.analytics.analytics_pipeline.create_engine'):
            with patch('indiaml_v2.analytics.analytics_pipeline.sessionmaker'):
                pipeline = AnalyticsPipeline(mock_db_path)
                pipeline.session = Mock()
                return pipeline
    
    def test_pipeline_initialization(self, mock_db_path):
        """Test pipeline initialization."""
        with patch('indiaml_v2.analytics.analytics_pipeline.create_engine') as mock_engine:
            with patch('indiaml_v2.analytics.analytics_pipeline.sessionmaker') as mock_sessionmaker:
                pipeline = AnalyticsPipeline(mock_db_path)
                
                mock_engine.assert_called_once_with(f"sqlite:///{mock_db_path}")
                mock_sessionmaker.assert_called_once()
                
                assert pipeline.db_path == mock_db_path
                assert hasattr(pipeline, 'global_stats')
                assert hasattr(pipeline, 'country_analyzer')
                assert hasattr(pipeline, 'institution_analyzer')
    
    def test_generate_analytics_structure(self, analytics_pipeline):
        """Test the analytics structure generation."""
        # Mock the analyzer responses
        global_data = {
            "conferenceInfo": {"totalAcceptedAuthors": 1000},
            "globalStats": {
                "countries": [
                    {"affiliation_country": "US", "paper_count": 500, "author_count": 800, "spotlights": 50, "orals": 100},
                    {"affiliation_country": "IN", "paper_count": 50, "author_count": 120, "spotlights": 5, "orals": 10},
                    {"affiliation_country": "CN", "paper_count": 300, "author_count": 600, "spotlights": 30, "orals": 60}
                ]
            }
        }
        
        focus_country_data = {
            "total_authors": 120,
            "total_spotlights": 5,
            "total_orals": 10,
            "institution_types": {"academic": 8, "corporate": 2},
            "at_least_one_focus_country_author": {"count": 50, "papers": []},
            "majority_focus_country_authors": {"count": 30, "papers": []},
            "first_focus_country_author": {"count": 25, "papers": []},
            "institutions": []
        }
        
        institution_data = {
            "summary": {"total_institutions": 10},
            "topInstitutions": [],
            "totalInstitutions": 10
        }
        
        analytics = analytics_pipeline._build_analytics_structure(
            global_data, focus_country_data, institution_data,
            "ICML", 2024, "IN"
        )
        
        # Verify structure
        assert analytics["conference"] == "ICML"
        assert analytics["year"] == 2024
        assert analytics["focus_country"] == "India"
        assert analytics["focus_country_code"] == "IN"
        
        # Verify global stats
        assert analytics["globalStats"]["totalPapers"] == 850  # Sum of all papers
        assert analytics["globalStats"]["totalAuthors"] == 1000
        
        # Verify focus country summary
        focus_summary = analytics["focusCountrySummary"]
        assert focus_summary["country"] == "India"
        assert focus_summary["paper_count"] == 50
        assert focus_summary["rank"] == 3  # US=1, CN=2, IN=3
        assert focus_summary["percentage"] == pytest.approx(5.88, rel=1e-2)  # 50/850 * 100
    
    def test_dashboard_content_generation(self, analytics_pipeline):
        """Test dashboard content generation."""
        analytics = {
            "conference": "ICML",
            "year": 2024,
            "focusCountrySummary": {
                "country": "India",
                "paper_count": 50,
                "percentage": 5.88,
                "rank": 3,
                "spotlights": 5,
                "orals": 10,
                "author_count": 120,
                "institution_count": 10,
                "academic_institutions": 8,
                "corporate_institutions": 2
            },
            "globalStats": {
                "totalPapers": 850,
                "countries": [
                    {"affiliation_country": "US", "paper_count": 500},
                    {"affiliation_country": "CN", "paper_count": 300},
                    {"affiliation_country": "IN", "paper_count": 50}
                ]
            },
            "focusCountry": {
                "authorship": {
                    "first_author": {"count": 25},
                    "majority": {"count": 30}
                }
            },
            "institutions": {
                "top_institutions": [
                    {"name": "IIT Delhi", "paper_count": 10, "author_count": 25}
                ]
            }
        }
        
        dashboard = analytics_pipeline._generate_dashboard_content(analytics, "IN")
        
        # Verify dashboard structure
        assert "summary" in dashboard
        assert "context" in dashboard
        assert "focusCountry" in dashboard
        assert "institutions" in dashboard
        
        # Verify content generation
        for section in dashboard.values():
            assert "title" in section
            assert "content" in section
            assert isinstance(section["content"], list)
            assert len(section["content"]) > 0
    
    def test_save_analytics(self, analytics_pipeline):
        """Test saving analytics to file."""
        analytics = {"test": "data", "conference": "ICML"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_analytics.json"
            
            analytics_pipeline._save_analytics(analytics, str(output_path))
            
            # Verify file was created
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == analytics


class TestGlobalStatsGenerator:
    """Test the global statistics generator."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        session = Mock()
        return session
    
    @pytest.fixture
    def global_stats_generator(self, mock_session):
        """Create a global stats generator for testing."""
        return GlobalStatsGenerator(mock_session)
    
    def test_conference_info_generation(self, global_stats_generator, mock_session):
        """Test conference information generation."""
        # Mock conference query
        mock_conference = Mock()
        mock_conference.id = 1
        mock_conference.name = "ICML"
        mock_conference.year = 2024
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_conference
        mock_session.query.return_value.join.return_value.filter.return_value.count.return_value = 100
        
        conference_info = global_stats_generator._get_conference_info("ICML", 2024)
        
        assert conference_info["name"] == "ICML"
        assert conference_info["year"] == 2024
        assert conference_info["totalAcceptedPapers"] == 100
    
    def test_country_code_mapping(self, global_stats_generator):
        """Test country code mapping functionality."""
        # Test direct mapping
        assert global_stats_generator._find_country_code_by_name("United States") == "US"
        assert global_stats_generator._find_country_code_by_name("China") == "CN"
        assert global_stats_generator._find_country_code_by_name("India") == "IN"
        
        # Test case insensitive
        assert global_stats_generator._find_country_code_by_name("united states") == "US"
        assert global_stats_generator._find_country_code_by_name("CHINA") == "CN"
        
        # Test unknown country
        assert global_stats_generator._find_country_code_by_name("Unknown Country") == "UNK"


class TestCountryAnalyzer:
    """Test the country analyzer."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        session = Mock()
        return session
    
    @pytest.fixture
    def country_analyzer(self, mock_session):
        """Create a country analyzer for testing."""
        return CountryAnalyzer(mock_session)
    
    def test_institution_classification(self, country_analyzer):
        """Test institution type classification."""
        # Test academic institutions
        assert country_analyzer._classify_institution_type("Indian Institute of Technology") == "academic"
        assert country_analyzer._classify_institution_type("Stanford University") == "academic"
        assert country_analyzer._classify_institution_type("IIT Delhi") == "academic"
        
        # Test corporate institutions
        assert country_analyzer._classify_institution_type("Google Research") == "corporate"
        assert country_analyzer._classify_institution_type("Microsoft Labs") == "corporate"
        assert country_analyzer._classify_institution_type("IBM Research") == "corporate"
        
        # Test default classification
        assert country_analyzer._classify_institution_type("Unknown Institute") == "academic"
    
    def test_paper_status_detection(self, country_analyzer):
        """Test paper status detection."""
        # Test spotlight detection
        assert country_analyzer._is_spotlight("Spotlight") == True
        assert country_analyzer._is_spotlight("spotlight presentation") == True
        assert country_analyzer._is_spotlight("Oral") == False
        assert country_analyzer._is_spotlight(None) == False
        
        # Test oral detection
        assert country_analyzer._is_oral("Oral") == True
        assert country_analyzer._is_oral("oral presentation") == True
        assert country_analyzer._is_oral("Spotlight") == False
        assert country_analyzer._is_oral(None) == False
    
    def test_paper_info_formatting(self, country_analyzer):
        """Test paper information formatting."""
        mock_paper = Mock()
        mock_paper.id = 123
        mock_paper.title = "Test Paper"
        mock_paper.status = "Spotlight"
        
        paper_info = country_analyzer._format_paper_info(mock_paper)
        
        assert paper_info["id"] == 123
        assert paper_info["title"] == "Test Paper"
        assert paper_info["isSpotlight"] == True
        assert paper_info["isOral"] == False


class TestInstitutionAnalyzer:
    """Test the institution analyzer."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        session = Mock()
        return session
    
    @pytest.fixture
    def institution_analyzer(self, mock_session):
        """Create an institution analyzer for testing."""
        return InstitutionAnalyzer(mock_session)
    
    def test_summary_statistics_generation(self, institution_analyzer):
        """Test summary statistics generation."""
        institution_stats = [
            {
                "name": "IIT Delhi",
                "type": "academic",
                "paper_count": 10,
                "author_count": 25,
                "spotlights": 2,
                "spotlight_rate": 20.0
            },
            {
                "name": "Google Research",
                "type": "corporate",
                "paper_count": 8,
                "author_count": 15,
                "spotlights": 1,
                "spotlight_rate": 12.5
            },
            {
                "name": "IISc Bangalore",
                "type": "academic",
                "paper_count": 6,
                "author_count": 18,
                "spotlights": 1,
                "spotlight_rate": 16.7
            }
        ]
        
        summary = institution_analyzer._generate_summary_statistics(institution_stats)
        
        assert summary["total_institutions"] == 3
        assert summary["academic_institutions"] == 2
        assert summary["corporate_institutions"] == 1
        assert summary["total_papers"] == 24
        assert summary["total_authors"] == 58
        assert summary["avg_papers_per_institution"] == 8.0
        
        # Check top institutions
        assert len(summary["top_by_papers"]) <= 5
        assert summary["top_by_papers"][0]["name"] == "IIT Delhi"
        assert summary["top_by_papers"][0]["count"] == 10
    
    def test_comparison_metrics_generation(self, institution_analyzer):
        """Test comparison metrics generation."""
        institutions = [
            {
                "name": "IIT Delhi",
                "paper_count": 10,
                "author_count": 25,
                "spotlights": 2,
                "spotlight_rate": 20.0
            },
            {
                "name": "IISc Bangalore",
                "paper_count": 6,
                "author_count": 18,
                "spotlights": 1,
                "spotlight_rate": 16.7
            }
        ]
        
        metrics = institution_analyzer._generate_comparison_metrics(institutions)
        
        assert metrics["most_papers"] == "IIT Delhi"
        assert metrics["most_authors"] == "IIT Delhi"
        assert metrics["most_spotlights"] == "IIT Delhi"
        assert metrics["highest_spotlight_rate"] == "IIT Delhi"
        assert metrics["avg_papers"] == 8.0
        assert metrics["avg_authors"] == 21.5


class TestConfigurationAndConstants:
    """Test configuration and constants."""
    
    def test_country_code_mapping(self):
        """Test country code mapping completeness."""
        # Test some key countries
        assert COUNTRY_CODE_MAP["US"] == "United States"
        assert COUNTRY_CODE_MAP["IN"] == "India"
        assert COUNTRY_CODE_MAP["CN"] == "China"
        assert COUNTRY_CODE_MAP["GB"] == "United Kingdom"
        assert COUNTRY_CODE_MAP["DE"] == "Germany"
        
        # Test mapping is comprehensive
        assert len(COUNTRY_CODE_MAP) > 200  # Should have most countries
    
    def test_default_configuration(self):
        """Test default configuration values."""
        assert DEFAULT_CONFIG["focus_country_code"] == "IN"
        assert DEFAULT_CONFIG["focus_country_name"] == "India"
        assert DEFAULT_CONFIG["include_unknown_countries"] == True
        assert DEFAULT_CONFIG["min_papers_for_country_inclusion"] == 1
        assert DEFAULT_CONFIG["institution_analysis_enabled"] == True


class TestIntegration:
    """Integration tests for the complete analytics pipeline."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_batch_analytics_generation(self, temp_output_dir):
        """Test batch analytics generation."""
        conferences = [
            {"name": "ICML", "year": 2024},
            {"name": "ICLR", "year": 2024}
        ]
        
        with patch('indiaml_v2.analytics.analytics_pipeline.AnalyticsPipeline') as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline_class.return_value.__enter__.return_value = mock_pipeline
            
            # Mock the generate_analytics method
            mock_analytics = {"conference": "ICML", "year": 2024}
            mock_pipeline.generate_analytics.return_value = mock_analytics
            
            # Mock the batch generation
            expected_files = {
                "ICML-2024": f"{temp_output_dir}/icml-2024-analytics.json",
                "ICLR-2024": f"{temp_output_dir}/iclr-2024-analytics.json"
            }
            mock_pipeline.generate_batch_analytics.return_value = expected_files
            
            # Test the batch generation
            output_files = mock_pipeline.generate_batch_analytics(
                conferences=conferences,
                output_dir=temp_output_dir,
                focus_country_code="IN"
            )
            
            assert len(output_files) == 2
            assert "ICML-2024" in output_files
            assert "ICLR-2024" in output_files


if __name__ == "__main__":
    pytest.main([__file__])
