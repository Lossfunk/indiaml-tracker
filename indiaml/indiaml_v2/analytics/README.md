# IndiaML v2 Analytics Pipeline

This module provides comprehensive analytics generation for academic conference data using the v2 normalized database schema. It generates analytics JSON files compatible with the existing UI while leveraging the improved data structure.

## Overview

The analytics pipeline consists of several components that work together to generate detailed conference analytics:

- **Global Statistics Generator**: Generates country-level statistics across all conferences
- **Country Analyzer**: Provides detailed analysis for a specific focus country
- **Institution Analyzer**: Analyzes institutional contributions and rankings
- **Analytics Pipeline**: Orchestrates all components to generate complete analytics

## Features

### 🌍 Global Analytics
- Country-level paper and author counts
- Spotlight and oral presentation statistics
- Global rankings and distributions

### 🇮🇳 Focus Country Analysis
- Authorship pattern analysis (first author, majority authors, etc.)
- Institution breakdown within the focus country
- Paper categorization by acceptance type

### 🏛️ Institutional Analysis
- Institution rankings by various metrics
- Academic vs corporate classification
- Collaboration pattern analysis
- Productivity metrics

### 📊 Dashboard Generation
- Narrative descriptions of research impact
- Contextual analysis within global landscape
- Institutional excellence evaluation

## Quick Start

### Command Line Usage

```bash
# Generate analytics for a single conference
python -m indiaml_v2.pipeline.sqlite_to_analytics_json generate \
    data_v2/icml-v2.db ICML 2024 --country IN --output analytics/icml-2024-analytics.json

# Generate analytics for multiple conferences
python -m indiaml_v2.pipeline.sqlite_to_analytics_json batch \
    data_v2/icml-v2.db --conferences ICML:2024 ICLR:2024 --output analytics/

# Validate database structure
python -m indiaml_v2.pipeline.sqlite_to_analytics_json validate data_v2/icml-v2.db

# List available conferences
python -m indiaml_v2.pipeline.sqlite_to_analytics_json suggest-conferences data_v2/icml-v2.db
```

### Python API Usage

```python
from indiaml_v2.analytics import AnalyticsPipeline

# Generate analytics for a single conference
with AnalyticsPipeline("data_v2/icml-v2.db") as pipeline:
    analytics = pipeline.generate_analytics(
        conference_name="ICML",
        year=2024,
        focus_country_code="IN",
        output_path="analytics/icml-2024-analytics.json"
    )

# Generate analytics for multiple conferences
conferences = [
    {"name": "ICML", "year": 2024},
    {"name": "ICLR", "year": 2024},
    {"name": "NeurIPS", "year": 2024}
]

with AnalyticsPipeline("data_v2/conferences.db") as pipeline:
    output_files = pipeline.generate_batch_analytics(
        conferences=conferences,
        output_dir="analytics/",
        focus_country_code="IN"
    )
```

## Configuration

### Focus Country

The analytics pipeline supports any country code. Common examples:

- `IN` - India
- `US` - United States
- `CN` - China
- `GB` - United Kingdom
- `DE` - Germany
- `CA` - Canada
- `AU` - Australia
- `JP` - Japan
- `KR` - South Korea
- `SG` - Singapore

### Institution Classification

Institutions are automatically classified as:

- **Academic**: Universities, research institutes, colleges
- **Corporate**: Company research labs, industry R&D centers

The classification uses keyword matching and can be customized in `config.py`.

## Output Format

The generated analytics JSON follows this structure:

```json
{
  "conference": "ICML",
  "year": 2024,
  "focus_country": "India",
  "focus_country_code": "IN",
  "generated_at": "2024-01-01T00:00:00",
  
  "globalStats": {
    "totalPapers": 2500,
    "totalAuthors": 8000,
    "totalCountries": 65,
    "countries": [...]
  },
  
  "focusCountrySummary": {
    "country": "India",
    "rank": 8,
    "paper_count": 45,
    "author_count": 120,
    "percentage": 1.8,
    "spotlights": 3,
    "orals": 8
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
    "top_institutions": [...]
  },
  
  "dashboard": {
    "summary": {...},
    "context": {...},
    "focusCountry": {...},
    "institutions": {...}
  }
}
```

## Database Schema Requirements

The analytics pipeline requires the following tables in the v2 database schema:

### Core Tables
- `conferences` - Conference information
- `tracks` - Conference tracks/venues
- `papers` - Paper details
- `authors` - Author information
- `countries` - Country data with codes
- `institutions` - Institution information
- `affiliations` - Author-institution relationships

### Relationship Tables
- `paper_authors` - Paper-author relationships with ordering
- `paper_author_affiliations` - Links authors to their affiliations for specific papers

## Advanced Usage

### Custom Analytics Configuration

```python
from indiaml_v2.analytics.config import DEFAULT_CONFIG

# Customize configuration
custom_config = DEFAULT_CONFIG.copy()
custom_config["focus_country_code"] = "CN"
custom_config["min_papers_for_country_inclusion"] = 5

# Use with pipeline
analytics = pipeline.generate_analytics(
    conference_name="ICML",
    year=2024,
    focus_country_code=custom_config["focus_country_code"]
)
```

### Batch Processing with Configuration File

Create a configuration file `conferences.json`:

```json
{
  "database_path": "data_v2/all_conferences.db",
  "focus_country_code": "IN",
  "conferences": [
    {"name": "ICML", "year": 2024},
    {"name": "ICLR", "year": 2024},
    {"name": "NeurIPS", "year": 2024},
    {"name": "ICLR", "year": 2025}
  ]
}
```

Then run:

```bash
python -m indiaml_v2.pipeline.sqlite_to_analytics_json config conferences.json analytics/
```

### Institution Analysis

```python
from indiaml_v2.analytics import InstitutionAnalyzer

with AnalyticsPipeline("data_v2/icml-v2.db") as pipeline:
    institution_analyzer = pipeline.institution_analyzer
    
    # Get institution rankings
    rankings = institution_analyzer.get_institution_rankings(
        conference_name="ICML",
        year=2024,
        country_code="IN"
    )
    
    # Compare specific institutions
    comparison = institution_analyzer.compare_institutions(
        institution_names=["IIT Delhi", "IISc Bangalore", "Google Research"],
        conference_name="ICML",
        year=2024
    )
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Validate database first
   python -m indiaml_v2.pipeline.sqlite_to_analytics_json validate data_v2/icml-v2.db
   ```

2. **Missing Conference Data**
   ```bash
   # Check available conferences
   python -m indiaml_v2.pipeline.sqlite_to_analytics_json suggest-conferences data_v2/icml-v2.db
   ```

3. **Country Code Issues**
   ```bash
   # List available countries
   python -m indiaml_v2.pipeline.sqlite_to_analytics_json suggest-countries data_v2/icml-v2.db
   ```

### Logging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your analytics code here
```

## Performance Considerations

- **Database Indexing**: Ensure proper indexes on foreign key columns
- **Memory Usage**: Large conferences may require significant memory for processing
- **Batch Processing**: Use batch mode for multiple conferences to reuse database connections

## Contributing

When adding new analytics features:

1. Add new analyzer classes to the `analytics/` directory
2. Update the main `AnalyticsPipeline` to integrate new features
3. Add corresponding CLI commands to `sqlite_to_analytics_json.py`
4. Update this README with new functionality

## Version History

- **v2.0.0**: Initial release with v2 database schema support
- Comprehensive analytics generation
- Dashboard content generation
- Batch processing capabilities
- CLI interface with validation and suggestions
