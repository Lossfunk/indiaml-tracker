"""
Analytics module for generating comprehensive conference analytics from v2 database schema.

This module provides tools for analyzing academic conference data, generating
country-specific insights, institutional analysis, and global statistics.
"""

from .analytics_pipeline import AnalyticsPipeline
from .global_stats_generator import GlobalStatsGenerator
from .country_analyzer import CountryAnalyzer
from .institution_analyzer import InstitutionAnalyzer
from .config import (
    COUNTRY_CODE_MAP,
    APAC_COUNTRIES,
    COLOR_SCHEME,
    DEFAULT_CONFIG,
    DASHBOARD_SECTIONS
)

__version__ = "2.0.0"
__author__ = "IndiaML Analytics Team"

__all__ = [
    "AnalyticsPipeline",
    "GlobalStatsGenerator", 
    "CountryAnalyzer",
    "InstitutionAnalyzer",
    "COUNTRY_CODE_MAP",
    "APAC_COUNTRIES",
    "COLOR_SCHEME",
    "DEFAULT_CONFIG",
    "DASHBOARD_SECTIONS"
]
