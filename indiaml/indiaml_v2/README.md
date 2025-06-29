# IndiaML v2 - Academic Paper Analysis System

A robust ETL pipeline for importing and analyzing academic paper data from major ML/AI conferences.

## Quick Start

### Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### Basic Usage
```bash
# Import paperlist data
python pipeline/paperlist_importer.py data.json

# Custom database location
python pipeline/paperlist_importer.py data.json --database custom.db

# Debug logging
python pipeline/paperlist_importer.py data.json --log-level DEBUG
```

### CLI Options
```bash
python pipeline/paperlist_importer.py <json_file> [options]

Required:
  json_file                 Path to JSON file containing paperlist data

Optional:
  --database, -d DATABASE   Path to SQLite database file
  --config, -c CONFIG       Path to configuration JSON file  
  --log-level, -l LEVEL     Logging level (DEBUG/INFO/WARNING/ERROR)
```

## Features

- ✅ **CLI Support**: JSON file path as required argument
- ✅ **Configurable**: All constants moved to configuration file
- ✅ **25+ Conference Support**: ICML, NeurIPS, ICLR, AAAI, ACL, CVPR, etc.
- ✅ **Flexible Database**: Configurable database path
- ✅ **Enhanced Logging**: Detailed logging with configurable levels
- ✅ **Comprehensive Schema**: Normalized database with papers, authors, institutions, reviews, citations

## Configuration

The system uses `config.py` for all configuration settings:

```python
class ImporterConfig(BaseModel):
    # Database settings
    database_url: str = "sqlite:///paperlists.db"
    
    # Processing settings
    batch_size: int = 10
    verification_sample_size: int = 10
    max_author_id_attempts: int = 1000
    top_countries_limit: int = 5
    
    # Conference mappings (25+ conferences supported)
    conference_full_names: Dict[str, str] = {...}
```

## Files Structure

```
indiaml_v2/
├── config.py                    # Configuration classes and settings
├── pipeline/
│   └── paperlist_importer.py   # Main ETL script
├── models/
│   └── models.py               # SQLAlchemy database models
└── logs/                       # Generated log files
```

## Supported Conferences

**AI/ML Core**: AAAI, ICML, NeurIPS, ICLR, IJCAI, AISTATS, ACML, AutoML, UAI  
**NLP**: ACL, EMNLP, NAACL, COLING, COLM  
**Computer Vision**: CVPR, ICCV, ECCV, WACV  
**Graphics**: SIGGRAPH, SIGGRAPHASIA  
**Robotics**: ICRA, IROS, RSS, CORL  
**Data Mining**: KDD, WWW, ACMMM  
**Theory**: COLT  

## Examples

### Import ICML 2024 Data
```bash
python pipeline/paperlist_importer.py icml2024.json --database icml2024.db
```

### Import with Debug Logging
```bash
python pipeline/paperlist_importer.py data.json --log-level DEBUG
```

### Custom Configuration
```bash
python pipeline/paperlist_importer.py data.json --config custom_config.json
```

## Output

The script creates:
- **SQLite Database**: Normalized schema with comprehensive indexing
- **Log Files**: Detailed processing logs in `logs/` directory
- **Statistics Report**: Processing metrics and database statistics

## Migration from Hardcoded Version

### Before (Hardcoded)
```python
transformer = PaperlistsTransformer("sqlite:///paperlists.db")
main()  # Used hardcoded 'paperlists_data.json'
```

### After (Configurable)
```bash
python paperlist_importer.py your_data.json --database your_db.db
```

## 📚 Comprehensive Documentation

For detailed documentation, see the **[docs/indiaml_v2/](../../docs/indiaml_v2/)** directory:

- **[Complete Documentation](../../docs/indiaml_v2/README.md)** - System overview and architecture
- **[Database Schema](../../docs/indiaml_v2/DATABASE_SCHEMA.md)** - Complete schema reference with all tables and relationships
- **[Processing Script](../../docs/indiaml_v2/PROCESSING_SCRIPT.md)** - ETL pipeline documentation and paperlists schema
- **[Common Queries](../../docs/indiaml_v2/COMMON_QUERIES.md)** - SQL examples for research analytics
- **[Models Documentation](../../docs/indiaml_v2/MODELS.md)** - SQLAlchemy model definitions

## Database Schema Overview

The system creates a comprehensive normalized database with:

### Core Tables
- **Papers**: Academic papers with metadata, URLs, abstracts
- **Authors**: Researchers with profiles and external links  
- **Institutions**: Academic and research institutions
- **Countries**: Geographic locations
- **Conferences/Tracks**: Conference and track information

### Analytics Tables
- **Reviews**: Individual reviews and aggregated statistics
- **Citations**: Citation metrics from Google Scholar
- **Keywords**: Paper topics and research areas
- **Affiliations**: Author-institution relationships

### Key Relationships
- Papers ↔ Authors (many-to-many with ordering)
- Authors ↔ Institutions (many-to-many with roles)
- Papers → Reviews/Citations (one-to-many)
- Institutions → Countries (many-to-one)

## Performance & Logging

### Processing Performance
- **Batch Processing**: Configurable batch sizes (default: 10)
- **Progress Tracking**: Real-time progress and time estimation
- **Memory Efficient**: Individual paper commits with session management

### Comprehensive Logging
- **Main Log**: `paperlist_importer_main.log`
- **Error Log**: `paperlist_importer_main_errors.log`  
- **Performance Log**: `paperlist_importer_main_performance.log`

### Statistics Reporting
```
📊 Final Database Statistics:
  Papers: 1,234
  Authors: 5,678
  Institutions: 890
  Countries: 45

⚡ Performance Metrics:
  Total processing time: 45.67 seconds
  Papers processed per second: 27.03
```

## Troubleshooting

### Common Issues
- **Memory Issues**: Reduce `batch_size` in config
- **Slow Performance**: Check database indexes, reduce `verification_sample_size`
- **Data Quality**: Use `--log-level DEBUG` for detailed diagnostics

### Debug Mode
```bash
python paperlist_importer.py data.json --log-level DEBUG
```

## Backward Compatibility

Legacy functions still work but show deprecation warnings:
```python
# Still works but deprecated
main_with_custom_file("data.json", "custom.db")
```

---

**For complete documentation, examples, and advanced usage, see [docs/indiaml_v2/](../../docs/indiaml_v2/README.md)**
