"""
Configuration settings for the paperlist importer.

This module provides configuration classes using Pydantic for type safety
and validation of all configurable parameters.
"""

from pydantic import BaseModel
from typing import Dict, Optional


class ImporterConfig(BaseModel):
    """Configuration for the paperlist importer with comprehensive settings."""
    
    # Database settings
    database_url: str = "sqlite:///paperlists.db"
    
    # Logging settings
    log_directory: str = "logs"
    
    # Processing settings
    batch_size: int = 10
    max_retries: int = 3
    
    # Performance thresholds (in seconds)
    slow_operation_threshold: float = 10.0
    warning_operation_threshold: float = 1.0
    
    # Database optimization settings
    enable_indexes: bool = True
    session_autoflush: bool = False
    session_expire_on_commit: bool = False
    
    # Verification and sampling settings
    verification_sample_size: int = 10
    max_author_id_attempts: int = 1000
    top_countries_limit: int = 5
    
    # Comprehensive conference mappings
    conference_full_names: Dict[str, str] = {
        # AI/ML Core Conferences
        "AAAI": "Association for the Advancement of Artificial Intelligence",
        "ICML": "International Conference on Machine Learning",
        "NeurIPS": "Conference on Neural Information Processing Systems",
        "ICLR": "International Conference on Learning Representations",
        "IJCAI": "International Joint Conference on Artificial Intelligence",
        "AISTATS": "International Conference on Artificial Intelligence and Statistics",
        "ACML": "Asian Conference on Machine Learning",
        "AutoML": "International Conference on Automated Machine Learning",
        "UAI": "Conference on Uncertainty in Artificial Intelligence",
        
        # NLP Conferences
        "ACL": "Annual Meeting of the Association for Computational Linguistics",
        "EMNLP": "Conference on Empirical Methods in Natural Language Processing",
        "NAACL": "North American Chapter of the Association for Computational Linguistics",
        "COLING": "International Conference on Computational Linguistics",
        "COLM": "Conference on Language Modeling",
        
        # Computer Vision
        "CVPR": "Conference on Computer Vision and Pattern Recognition",
        "ICCV": "International Conference on Computer Vision",
        "ECCV": "European Conference on Computer Vision",
        "WACV": "Winter Conference on Applications of Computer Vision",
        
        # Graphics
        "SIGGRAPH": "Special Interest Group on Computer Graphics and Interactive Techniques",
        "SIGGRAPHASIA": "SIGGRAPH Asia",
        
        # Robotics
        "ICRA": "International Conference on Robotics and Automation",
        "IROS": "International Conference on Intelligent Robots and Systems",
        "RSS": "Robotics: Science and Systems",
        "CORL": "Conference on Robot Learning",
        
        # Data Mining/Web
        "KDD": "Knowledge Discovery and Data Mining",
        "WWW": "The Web Conference",
        "ACMMM": "ACM International Conference on Multimedia",
        
        # Theory
        "COLT": "Conference on Learning Theory"
    }
    
    # Track classification settings
    track_classifications: Dict[str, str] = {
        "main": "main",
        "position": "position",
        "workshop": "workshop",
        "tutorial": "tutorial",
        "demo": "demo",
        "poster": "poster_session"
    }
    
    # Default track names
    default_track_names: Dict[str, str] = {
        "main": "Main Conference",
        "position": "Position Papers",
        "workshop": "Workshop",
        "tutorial": "Tutorial",
        "demo": "Demonstration",
        "poster_session": "Poster Session"
    }


def load_config(config_path: Optional[str] = None) -> ImporterConfig:
    """
    Load configuration from file or return default configuration.
    
    Args:
        config_path: Optional path to JSON config file
        
    Returns:
        ImporterConfig instance
    """
    if config_path:
        try:
            import json
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return ImporterConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
            print("Using default configuration")
    
    return ImporterConfig()
