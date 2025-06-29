"""
Configuration Management for Tweet Generation Pipeline

Handles configuration from environment variables, CLI arguments, and config files.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class PipelineConfig:
    """Configuration manager for the tweet generation pipeline."""
    
    def __init__(self, conference: str, **kwargs):
        self.conference = conference
        
        # Load environment variables
        load_dotenv()
        
        # Set default paths (can be overridden)
        self.data_dir = Path(kwargs.get('data_dir', os.getenv('DATA_DIR', 'data')))
        self.analytics_dir = Path(kwargs.get('analytics_dir', 
                                           os.getenv('ANALYTICS_DIR', 'ui/indiaml-tracker/public/tracker')))
        self.output_dir = Path(kwargs.get('output_dir', 
                                        os.getenv('OUTPUT_DIR', 'eda/tweetgen/outputs')))
        
        # Database and analytics file patterns (configurable)
        self.db_pattern = kwargs.get('db_pattern', 
                                   os.getenv('DB_PATTERN', 'venues-{conference}-{version}.db'))
        self.analytics_pattern = kwargs.get('analytics_pattern',
                                          os.getenv('ANALYTICS_PATTERN', '{conference}-analytics.json'))
        
        # Processing settings
        self.max_concurrent_requests = int(kwargs.get('max_concurrent', 
                                                    os.getenv('MAX_CONCURRENT_REQUESTS', '3')))
        self.request_timeout = int(kwargs.get('request_timeout',
                                            os.getenv('REQUEST_TIMEOUT', '30')))
        self.rate_limit_delay = float(kwargs.get('rate_limit_delay',
                                                os.getenv('RATE_LIMIT_DELAY', '2.0')))
        
        # Tweet generation settings
        self.max_tweet_length = int(kwargs.get('max_tweet_length',
                                             os.getenv('MAX_TWEET_LENGTH', '280')))
        self.max_authors_per_tweet = int(kwargs.get('max_authors_per_tweet',
                                                  os.getenv('MAX_AUTHORS_PER_TWEET', '5')))
        
        # API settings
        self.openrouter_api_key = kwargs.get('openrouter_api_key', 
                                           os.getenv('OPENROUTER_API_KEY'))
        self.openrouter_base_url = kwargs.get('openrouter_base_url',
                                            os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1'))
        self.openrouter_model = kwargs.get('openrouter_model',
                                         os.getenv('OPENROUTER_MODEL', 'gpt-4o-mini'))
        self.openai_api_key = kwargs.get('openai_api_key',
                                       os.getenv('OPENAI_API_KEY'))
        
        # Conference-specific overrides
        self.conference_overrides = kwargs.get('conference_overrides', {})
        
        # Load conference mappings
        self._load_conference_mappings()
    
    def _load_conference_mappings(self):
        """Load conference mappings from config file or environment."""
        # Try to load from config file first
        config_file = Path('eda/tweetgen/conference_config.json')
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self.conference_mappings = json.load(f)
                return
            except Exception:
                pass
        
        # Fallback to default mappings
        self.conference_mappings = {
            "icml-2025": {
                "sqlite_file": "venues-icml-2025-v2.db",
                "analytics_file": "icml-2025-analytics.json",
                "version": "v2"
            },
            "icml-2024": {
                "sqlite_file": "venues-icml-2024-v2.1.db",
                "analytics_file": "icml-2024-analytics.json",
                "version": "v2.1"
            },
            "iclr-2025": {
                "sqlite_file": "venues-iclr-2025-v3.db",
                "analytics_file": "iclr-2025-analytics.json",
                "version": "v3"
            },
            "iclr-2024": {
                "sqlite_file": "venues-iclr-2024-v3.1.db",
                "analytics_file": "iclr-2024-analytics.json",
                "version": "v3.1"
            },
            "neurips-2024": {
                "sqlite_file": "venues-neurips-2024-v2.1.db",
                "analytics_file": "neurips-2024-analytics.json",
                "version": "v2.1"
            }
        }
    
    def get_conference_config(self) -> Dict[str, str]:
        """Get configuration for the specified conference."""
        if self.conference not in self.conference_mappings:
            # Try to auto-detect files if conference not in mappings
            return self._auto_detect_conference_files()
        
        config = self.conference_mappings[self.conference].copy()
        
        # Apply any overrides
        if self.conference in self.conference_overrides:
            config.update(self.conference_overrides[self.conference])
        
        return config
    
    def _auto_detect_conference_files(self) -> Dict[str, str]:
        """Auto-detect conference files based on patterns."""
        # Try to find database file
        db_candidates = list(self.data_dir.glob(f"*{self.conference}*.db"))
        if not db_candidates:
            raise FileNotFoundError(f"No database file found for conference: {self.conference}")
        
        # Use the most recent version (assuming higher version numbers are later)
        db_file = sorted(db_candidates)[-1]
        
        # Try to find analytics file
        analytics_candidates = list(self.analytics_dir.glob(f"{self.conference}*analytics*.json"))
        if not analytics_candidates:
            raise FileNotFoundError(f"No analytics file found for conference: {self.conference}")
        
        analytics_file = analytics_candidates[0]  # Assume first match is correct
        
        return {
            "sqlite_file": db_file.name,
            "analytics_file": analytics_file.name,
            "version": "auto-detected"
        }
    
    def get_sqlite_path(self) -> Path:
        """Get full path to SQLite database."""
        config = self.get_conference_config()
        return self.data_dir / config["sqlite_file"]
    
    def get_analytics_path(self) -> Path:
        """Get full path to analytics file."""
        config = self.get_conference_config()
        return self.analytics_dir / config["analytics_file"]
    
    def get_json_path(self) -> Path:
        """Get full path to JSON data file."""
        # Look for JSON files matching the conference pattern
        patterns = [
            f"{self.conference}.json",
            f"*{self.conference}*.json"
        ]
        
        for pattern in patterns:
            matches = list(self.analytics_dir.glob(pattern))
            if matches:
                # Return the first match (should be the main data file)
                return matches[0]
        
        raise FileNotFoundError(f"No JSON file found for conference '{self.conference}' in {self.analytics_dir}")
    
    def get_output_path(self) -> Path:
        """Get output directory for this conference."""
        return self.output_dir / self.conference
    
    def validate_paths(self) -> None:
        """Validate that all required paths exist."""
        sqlite_path = self.get_sqlite_path()
        if not sqlite_path.exists():
            raise FileNotFoundError(f"SQLite file not found: {sqlite_path}")
        
        analytics_path = self.get_analytics_path()
        if not analytics_path.exists():
            raise FileNotFoundError(f"Analytics file not found: {analytics_path}")
    
    def has_api_keys(self) -> bool:
        """Check if API keys are available."""
        return bool(self.openrouter_api_key or self.openai_api_key)
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        if self.openrouter_api_key:
            return {
                "type": "openrouter",
                "api_key": self.openrouter_api_key,
                "base_url": self.openrouter_base_url,
                "model": self.openrouter_model
            }
        elif self.openai_api_key:
            return {
                "type": "openai",
                "api_key": self.openai_api_key,
                "model": "gpt-4o-mini"
            }
        else:
            return {"type": "none"}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "conference": self.conference,
            "data_dir": str(self.data_dir),
            "analytics_dir": str(self.analytics_dir),
            "output_dir": str(self.output_dir),
            "sqlite_path": str(self.get_sqlite_path()),
            "analytics_path": str(self.get_analytics_path()),
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_timeout": self.request_timeout,
            "rate_limit_delay": self.rate_limit_delay,
            "max_tweet_length": self.max_tweet_length,
            "max_authors_per_tweet": self.max_authors_per_tweet,
            "has_api_keys": self.has_api_keys(),
            "api_config": self.get_api_config()
        }
    
    @classmethod
    def from_cli_args(cls, args) -> 'PipelineConfig':
        """Create configuration from CLI arguments."""
        kwargs = {}
        
        # Map CLI arguments to config parameters
        if hasattr(args, 'data_dir') and args.data_dir:
            kwargs['data_dir'] = args.data_dir
        if hasattr(args, 'analytics_dir') and args.analytics_dir:
            kwargs['analytics_dir'] = args.analytics_dir
        if hasattr(args, 'output_dir') and args.output_dir:
            kwargs['output_dir'] = args.output_dir
        if hasattr(args, 'max_concurrent') and args.max_concurrent:
            kwargs['max_concurrent'] = args.max_concurrent
        if hasattr(args, 'request_timeout') and args.request_timeout:
            kwargs['request_timeout'] = args.request_timeout
        if hasattr(args, 'max_tweet_length') and args.max_tweet_length:
            kwargs['max_tweet_length'] = args.max_tweet_length
        
        return cls(args.conference, **kwargs)


def load_conference_config_file(config_path: str = 'eda/tweetgen/conference_config.json') -> Dict[str, Any]:
    """Load conference configuration from JSON file."""
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}


def save_conference_config_file(config: Dict[str, Any], 
                               config_path: str = 'eda/tweetgen/conference_config.json') -> None:
    """Save conference configuration to JSON file."""
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
