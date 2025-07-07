# IndiaML v2 Analytics Pipeline - Complete Implementation

## Overview

The IndiaML v2 analytics pipeline has been successfully implemented to replicate the v1 analytics functionality while working with the new v2 database schema. This pipeline generates comprehensive analytics JSON files compatible with the existing UI tracker system.

## Architecture

### Core Components

1. **Analytics Pipeline** (`analytics_pipeline.py`)
   - Main orchestrator that coordinates all analytics generation
   - Handles database connections and session management
   - Generates complete analytics JSON files

2. **Global Stats Generator** (`global_stats_generator.py`)
   - Generates conference-wide statistics
   - Calculates total papers, authors, and country distributions
   - Provides global context for analytics

3. **Country Analyzer** (`country_analyzer.py`)
   - Analyzes focus country performance
   - Calculates authorship patterns (first author, majority, at least one)
   - Generates country-specific insights

4. **Institution Analyzer** (`institution_analyzer.py`)
   - Analyzes institutional performance within focus country
   - Categorizes institutions (academic vs corporate)
   - Ranks institutions by paper count

5. **Configuration** (`config.py`)
   - Centralized configuration for colors, country mappings
   - Dashboard content templates
   - Default settings and constants

### Database Schema Compatibility

The pipeline works with the v2 database schema which includes:
- `papers` - Paper information with normalized status
- `authors` - Author details
- `affiliations` - Author-institution relationships
- `institutions` - Institution information
- `countries` - Country data with ISO codes
- `conferences` - Conference metadata
- `paper_authors` - Paper-author relationships

## Generated Analytics Structure

Each analytics file contains:

```json
{
  "conference": "ICML",
  "year": 2024,
  "focus_country": "India",
  "focus_country_code": "IN",
  "globalStats": {
    "totalPapers": 2500,
    "totalAuthors": 8000,
    "totalCountries": 65,
    "countries": [...]
  },
  "focusCountrySummary": {
    "country": "India",
    "country_code": "IN",
    "rank": 17,
    "paper_count": 22,
    "author_count": 45,
    "percentage": 0.88,
    "spotlights": 2,
    "orals": 1,
    "institution_count": 15,
    "academic_institutions": 12,
    "corporate_institutions": 3
  },
  "focusCountry": {
    "authorship": {
      "at_least_one": {...},
      "majority": {...},
      "first_author": {...}
    },
    "institutions": [...]
  },
  "institutions": {
    "summary": {...},
    "top_institutions": [...],
    "total_institutions": 15
  },
  "dashboard": {
    "overview": {...},
    "performance": {...},
    "institutions": {...},
    "comparison": {...}
  },
  "config": {
    "focus_country_code": "IN",
    "focus_country_name": "India",
    "colors": {...}
  }
}
```

## Usage

### Command Line Interface

```bash
# Generate analytics for a specific conference
cd indiaml && python -m indiaml_v2.pipeline.sqlite_to_analytics_json generate \
  ../data_v2/icml-v2.db ICML 2024 \
  --country IN \
  --output ../ui/indiaml-tracker/public/tracker_v2/icml-v2/icml-2024-analytics.json

# Generate analytics for ICLR 2024
cd indiaml && python -m indiaml_v2.pipeline.sqlite_to_analytics_json generate \
  ../data_v2/iclr-v1.db ICLR 2024 \
  --country IN \
  --output ../ui/indiaml-tracker/public/tracker_v2/iclr-v1/iclr-2024-analytics.json

# Generate analytics for NeurIPS 2024
cd indiaml && python -m indiaml_v2.pipeline.sqlite_to_analytics_json generate \
  ../data_v2/neurips_v1.4.db NeurIPS 2024 \
  --country IN \
  --output ../ui/indiaml-tracker/public/tracker_v2/neurips-v1/neurips-2024-analytics.json
```

### Programmatic Usage

```python
from indiaml_v2.analytics.analytics_pipeline import AnalyticsPipeline

# Initialize pipeline
pipeline = AnalyticsPipeline("path/to/database.db")

# Generate analytics
analytics = pipeline.generate_analytics(
    conference_name="ICML",
    year=2024,
    focus_country_code="IN",
    output_path="output/analytics.json"
)

# Close pipeline
pipeline.close()
```

## Generated Files

The pipeline has successfully generated analytics for:

### ICML 2024 (v2 database)
- **File**: `ui/indiaml-tracker/public/tracker_v2/icml-v2/icml-2024-analytics.json`
- **India Performance**: 22 papers, rank 17
- **Database**: `data_v2/icml-v2.db`

### ICLR 2024 (v1 database)
- **File**: `ui/indiaml-tracker/public/tracker_v2/iclr-v1/iclr-2024-analytics.json`
- **India Performance**: 87 papers, rank 16
- **Database**: `data_v2/iclr-v1.db`

### ICLR 2025 (v1 database)
- **File**: `ui/indiaml-tracker/public/tracker_v2/iclr-v1/iclr-2025-analytics.json`
- **India Performance**: 95 papers, rank 15
- **Database**: `data_v2/iclr-v1.db`

### NeurIPS 2024 (v1 database)
- **File**: `ui/indiaml-tracker/public/tracker_v2/neurips-v1/neurips-2024-analytics.json`
- **India Performance**: 36 papers, rank 17
- **Database**: `data_v2/neurips_v1.4.db`

## Tracker Integration

The analytics files are integrated into the UI tracker system via:

**Index File**: `ui/indiaml-tracker/public/tracker_v2/index.json`

```json
[
  {
    "label": "ICML 2024 v2",
    "file": "icml-2024-v2.json",
    "analytics": "icml-v2/icml-2024-analytics.json",
    "venue": "icml",
    "year": "2024",
    "sqlite_file": "icml-v2.db"
  },
  {
    "label": "ICLR 2024 v1",
    "file": "iclr-2024-v1.json",
    "analytics": "iclr-v1/iclr-2024-analytics.json",
    "venue": "iclr",
    "year": "2024",
    "sqlite_file": "iclr-v1.db"
  },
  {
    "label": "ICLR 2025 v1",
    "file": "iclr-2025-v1.json",
    "analytics": "iclr-v1/iclr-2025-analytics.json",
    "venue": "iclr",
    "year": "2025",
    "sqlite_file": "iclr-v1.db"
  },
  {
    "label": "NeurIPS 2024 v1",
    "file": "neurips-2024-v1.json",
    "analytics": "neurips-v1/neurips-2024-analytics.json",
    "venue": "neurips",
    "year": "2024",
    "sqlite_file": "neurips_v1.4.db"
  }
]
```

## Testing

Comprehensive test suite available at `indiaml_v2/tests/test_v2_analytics_pipeline.py`:

```bash
# Run all tests
cd indiaml && python -m indiaml_v2.tests.test_v2_analytics_pipeline
```

**Test Results**:
- ✅ All 6 tests passed
- ✅ Analytics file structure validation
- ✅ Country code mapping verification
- ✅ Multi-conference analytics generation
- ✅ Multi-country analytics generation

## Key Features

1. **Database Schema Agnostic**: Works with both v1 and v2 database schemas
2. **Comprehensive Analytics**: Generates global stats, country analysis, and institution rankings
3. **Dashboard Integration**: Includes narrative dashboard content for UI display
4. **Flexible Configuration**: Supports different focus countries and conferences
5. **Robust Testing**: Full test coverage with validation of output structure
6. **CLI Interface**: Easy-to-use command line interface for batch processing
7. **Error Handling**: Comprehensive error handling and logging
8. **Performance Optimized**: Efficient database queries and data processing

## Performance Metrics

Based on test runs:
- **ICML 2024**: India ranks 17th with 22 papers
- **ICLR 2024**: India ranks 16th with 87 papers  
- **ICLR 2025**: India ranks 15th with 95 papers
- **NeurIPS 2024**: India ranks 17th with 36 papers

## Future Enhancements

1. **Batch Processing**: Add support for generating multiple analytics files in one command
2. **Caching**: Implement caching for frequently accessed data
3. **Visualization**: Add built-in chart generation capabilities
4. **API Integration**: Create REST API endpoints for real-time analytics
5. **Custom Metrics**: Support for user-defined analytics metrics

## Conclusion

The IndiaML v2 analytics pipeline successfully replicates and extends the functionality of the v1 system while providing better performance, maintainability, and extensibility. The pipeline is production-ready and fully integrated with the existing UI tracker system.
