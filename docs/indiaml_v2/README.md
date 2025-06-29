# IndiaML v2 Documentation

Comprehensive documentation for the IndiaML v2 academic paper analysis system.

## Overview

IndiaML v2 is a robust system for importing, storing, and analyzing academic paper data from major ML/AI conferences. It transforms raw paperlist JSON data into a normalized relational database optimized for research analytics.

## Key Features

- ✅ **Comprehensive Database Schema**: Normalized schema supporting papers, authors, institutions, reviews, citations
- ✅ **Robust ETL Pipeline**: Configurable import script with error handling and validation
- ✅ **25+ Conference Support**: Built-in support for major ML/AI conferences
- ✅ **CLI Interface**: Command-line tool with flexible configuration
- ✅ **Performance Optimized**: Indexed database with efficient query patterns
- ✅ **Comprehensive Logging**: Detailed logging and monitoring system

## Documentation Structure

### Core Documentation
- **[Database Schema](DATABASE_SCHEMA.md)** - Complete database schema documentation
- **[Processing Script](PROCESSING_SCRIPT.md)** - ETL pipeline and import script documentation
- **[Common Queries](COMMON_QUERIES.md)** - SQL query examples for common analytics tasks

### Quick Start
- **[Configuration Guide](../indiaml_v2/README.md)** - Setup and configuration instructions
- **[Models Documentation](MODELS.md)** - SQLAlchemy model definitions

## System Architecture

```
Raw JSON Data → ETL Pipeline → Normalized Database → Analytics Queries
     ↓              ↓              ↓                    ↓
Paperlist      Processing     SQLite Database     Research
Schema         Script         (IndiaML v2)        Analytics
```

### Data Flow

1. **Input**: JSON files with academic paper data (paperlist schema)
2. **Processing**: ETL pipeline transforms and validates data
3. **Storage**: Normalized relational database with comprehensive schema
4. **Analysis**: SQL queries for research analytics and insights

## Supported Conferences

The system supports 25+ major conferences including:

### AI/ML Core
- **AAAI** - Association for the Advancement of Artificial Intelligence
- **ICML** - International Conference on Machine Learning
- **NeurIPS** - Conference on Neural Information Processing Systems
- **ICLR** - International Conference on Learning Representations
- **IJCAI** - International Joint Conference on Artificial Intelligence
- **AISTATS** - International Conference on Artificial Intelligence and Statistics
- **ACML** - Asian Conference on Machine Learning
- **AutoML** - International Conference on Automated Machine Learning
- **UAI** - Conference on Uncertainty in Artificial Intelligence

### Natural Language Processing
- **ACL** - Association for Computational Linguistics
- **EMNLP** - Empirical Methods in Natural Language Processing
- **NAACL** - North American Chapter of the Association for Computational Linguistics
- **COLING** - International Conference on Computational Linguistics
- **COLM** - Conference on Language Modeling

### Computer Vision
- **CVPR** - Conference on Computer Vision and Pattern Recognition
- **ICCV** - International Conference on Computer Vision
- **ECCV** - European Conference on Computer Vision
- **WACV** - Winter Conference on Applications of Computer Vision

### Graphics and Visualization
- **SIGGRAPH** - Special Interest Group on Computer Graphics
- **SIGGRAPHASIA** - SIGGRAPH Asia

### Robotics
- **ICRA** - International Conference on Robotics and Automation
- **IROS** - International Conference on Intelligent Robots and Systems
- **RSS** - Robotics: Science and Systems
- **CORL** - Conference on Robot Learning

### Data Mining and Web
- **KDD** - Knowledge Discovery and Data Mining
- **WWW** - World Wide Web Conference
- **ACMMM** - ACM International Conference on Multimedia

### Theory
- **COLT** - Conference on Learning Theory

## Database Schema Overview

### Core Entities
- **Papers**: Academic papers with metadata, URLs, and content
- **Authors**: Researchers with profiles and external links
- **Institutions**: Academic and research institutions
- **Countries**: Geographic locations for institutions
- **Conferences**: Conference and venue information
- **Tracks**: Conference tracks (main, workshops, tutorials)

### Relationships
- **Paper-Author**: Many-to-many with author ordering
- **Author-Institution**: Many-to-many affiliations with roles
- **Paper-Keyword**: Many-to-many topic associations
- **Reviews**: Individual and aggregated review data
- **Citations**: Citation metrics and external links

### Analytics Support
- **Review Statistics**: Aggregated review metrics per paper
- **Citation Data**: Google Scholar and other citation sources
- **External Profiles**: Flexible author profile storage
- **Geographic Analysis**: Country and institution analytics

## Processing Pipeline

### ETL Stages

1. **Extract**: Load JSON data from paperlist files
2. **Transform**: 
   - Parse semicolon-separated fields
   - Normalize institution and author names
   - Extract conference and track information
   - Process review and citation data
3. **Load**: 
   - Create database entities with existence checking
   - Establish relationships
   - Validate data integrity
   - Generate performance indexes

### Key Features
- **Duplicate Detection**: Skip existing papers automatically
- **Error Recovery**: Individual paper failures don't stop processing
- **Progress Tracking**: Real-time progress and time estimation
- **Verification**: Post-import data validation and statistics

## Common Use Cases

### Research Analytics
- **Author Productivity**: Track publication counts and collaboration patterns
- **Institution Rankings**: Analyze institutional research output
- **Conference Trends**: Study conference participation and acceptance rates
- **Citation Analysis**: Examine citation patterns and impact metrics
- **Geographic Studies**: Analyze research distribution by country/region

### Collaboration Networks
- **Co-authorship Analysis**: Identify collaboration patterns
- **Institution Partnerships**: Find inter-institutional collaborations
- **International Cooperation**: Track cross-country research partnerships
- **Author Mobility**: Study researcher movement between institutions

### Review Process Analysis
- **Review Quality**: Analyze reviewer confidence and consistency
- **Acceptance Patterns**: Study factors affecting paper acceptance
- **Controversial Papers**: Identify papers with high review variance
- **Review Metrics**: Correlate review scores with citations

## Performance Characteristics

### Database Optimization
- **Indexed Lookups**: Fast queries on common fields
- **Compound Indexes**: Optimized for complex analytics
- **Normalized Schema**: Efficient storage and consistency
- **Query Patterns**: Optimized for research analytics

### Processing Performance
- **Batch Processing**: Configurable batch sizes for memory management
- **Parallel-Safe**: Individual paper processing with transaction isolation
- **Progress Monitoring**: Real-time performance metrics
- **Resource Management**: Efficient memory and database connection usage

## Configuration and Customization

### Flexible Configuration
- **Database Settings**: Custom database locations and connection parameters
- **Processing Parameters**: Batch sizes, verification settings, retry limits
- **Conference Support**: Easy addition of new conferences and tracks
- **Logging Configuration**: Customizable logging levels and destinations

### Extensibility
- **New Conferences**: Simple configuration additions
- **Custom Fields**: Extensible schema for additional metadata
- **External Profiles**: Flexible storage for new profile platforms
- **Analytics Extensions**: Easy addition of new query patterns

## Getting Started

### Prerequisites
- Python 3.8+
- SQLAlchemy
- Pydantic
- Required dependencies (see requirements.txt)

### Basic Usage
```bash
# Install dependencies
pip install -r requirements.txt

# Import data
python pipeline/paperlist_importer.py data.json

# Custom database
python pipeline/paperlist_importer.py data.json --database custom.db

# Debug mode
python pipeline/paperlist_importer.py data.json --log-level DEBUG
```

### Configuration
Edit `config.py` to customize:
- Database settings
- Processing parameters
- Conference mappings
- Logging configuration

## Documentation Navigation

- **[Database Schema](DATABASE_SCHEMA.md)** - Complete schema reference
- **[Processing Script](PROCESSING_SCRIPT.md)** - ETL pipeline documentation
- **[Common Queries](COMMON_QUERIES.md)** - SQL examples and patterns
- **[Models](MODELS.md)** - SQLAlchemy model definitions

## Support and Troubleshooting

### Common Issues
- **Memory Usage**: Adjust batch_size in configuration
- **Performance**: Check database indexes and query patterns
- **Data Quality**: Use debug logging to identify issues
- **Dependencies**: Ensure all required packages are installed

### Debug Resources
- **Comprehensive Logging**: Multiple log files with different detail levels
- **Verification System**: Post-import data validation
- **Statistics Reporting**: Detailed processing and database statistics
- **Error Handling**: Graceful handling of malformed data

## Contributing

### Adding New Conferences
1. Add conference mapping to `config.py`
2. Update track classifications if needed
3. Test with sample data
4. Update documentation

### Schema Extensions
1. Modify SQLAlchemy models in `models/models.py`
2. Update processing script for new fields
3. Add appropriate indexes
4. Update documentation and queries

### Query Contributions
1. Add new queries to `COMMON_QUERIES.md`
2. Include performance notes and optimization tips
3. Provide usage examples and expected results
