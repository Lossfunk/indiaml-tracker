# Paperlist Importer Processing Script Documentation

This document provides comprehensive documentation for the `paperlist_importer.py` script, which transforms raw paperlist JSON data into the normalized IndiaML v2 database schema.

## Overview

The paperlist importer is a robust ETL (Extract, Transform, Load) pipeline that:
1. **Extracts** data from JSON files containing academic paper information
2. **Transforms** the data into a normalized relational schema
3. **Loads** the data into SQLite databases with comprehensive validation

## Script Architecture

### Core Components

```python
# Main processing class
class PaperlistsTransformer:
    def __init__(self, config: ImporterConfig = None, database_url: str = None)
    def transform_paperlists_data(self, paperlists_json: List[Dict])
    def process_single_paper_with_checks(self, data: Dict)
```

### Configuration System

The script uses a comprehensive configuration system defined in `config.py`:

```python
class ImporterConfig(BaseModel):
    # Database settings
    database_url: str = "sqlite:///paperlists.db"
    
    # Processing settings
    batch_size: int = 10
    verification_sample_size: int = 10
    max_author_id_attempts: int = 1000
    top_countries_limit: int = 5
    
    # Session configuration
    session_autoflush: bool = True
    session_expire_on_commit: bool = False
    
    # Logging settings
    log_directory: str = "logs"
    slow_operation_threshold: float = 10.0
    warning_operation_threshold: float = 1.0
    
    # Conference mappings (25+ conferences)
    conference_full_names: Dict[str, str] = {...}
    track_classifications: Dict[str, str] = {...}
```

## Input Data Format (Paperlists Schema)

The script expects JSON data with the following structure for each paper:

### Core Paper Fields
```json
{
  "id": "3vjsUgCsZ4",                    // Unique paper identifier
  "title": "Paper Title",               // Paper title
  "status": "Poster",                   // "Poster", "Oral", "Spotlight"
  "track": "main",                      // Conference track
  "primary_area": "Machine Learning",   // Research area
  "abstract": "Paper abstract...",      // Full abstract
  "tldr": "Short summary...",          // Too Long; Didn't Read summary
  "bibtex": "@inproceedings{...}",     // BibTeX citation
  "site": "https://...",               // Conference site URL
  "openreview": "https://...",         // OpenReview URL
  "pdf": "https://...",                // PDF URL
  "github": "https://...",             // GitHub repository
  "project": "https://...",            // Project page
  "author_num": 3,                     // Number of authors
  "pdf_size": 1024000                  // PDF size in bytes
}
```

### Author Information
```json
{
  "author": "John Doe;Jane Smith;Bob Johnson",           // Semicolon-separated names
  "author_site": "J. Doe;J. Smith;B. Johnson",         // Names as on site
  "authorids": "john_doe;jane_smith;bob_johnson",       // Author IDs
  "gender": "M;F;M",                                    // Gender information
  "homepage": "https://johndoe.com;;https://bob.edu",  // Personal homepages
  "dblp": "john-doe;jane-smith;bob-johnson",           // DBLP IDs
  "google_scholar": "https://scholar.google.com/...;", // Google Scholar URLs
  "orcid": "0000-0000-0000-0001;;0000-0000-0000-0003", // ORCID identifiers
  "linkedin": "https://linkedin.com/in/johndoe;;",     // LinkedIn profiles
  "or_profile": "~John_Doe1;~Jane_Smith1;~Bob_Johnson1" // OpenReview profiles
}
```

### Affiliation Data
```json
{
  "aff": "MIT;Stanford University;Google",              // Raw affiliations
  "position": "PhD Student;Professor;Research Scientist", // Positions
  "aff_domain": "mit.edu;stanford.edu;google.com",     // Email domains
  
  // Normalized affiliation data
  "aff_unique_index": "0;1;2",                         // Affiliation indices
  "aff_unique_norm": "MIT;Stanford University;Google", // Normalized names
  "aff_unique_dep": "CSAIL;CS Department;Research",    // Departments
  "aff_unique_url": "https://mit.edu;https://stanford.edu;", // URLs
  "aff_unique_abbr": "MIT;Stanford;GOOG",             // Abbreviations
  
  // Country mapping
  "aff_country_unique_index": "0;0;0",                // Country indices
  "aff_country_unique": "United States",              // Country names
  
  // Campus information
  "aff_campus_unique_index": "0;1;2",                 // Campus indices
  "aff_campus_unique": "Cambridge;Palo Alto;Mountain View" // Campus names
}
```

### Review Data
```json
{
  "rating": "4;3;5",                    // Individual ratings (1-5)
  "confidence": "3;4;3",                // Reviewer confidence (1-5)
  "recommendation": "1;0;1",            // Accept/reject recommendations
  "reviewers": "rev1;rev2;rev3",        // Anonymous reviewer IDs
  
  // Aggregated statistics
  "rating_avg": [4.0, 1.0],            // [mean, std] for ratings
  "confidence_avg": [3.33, 0.58],      // [mean, std] for confidence
  "support_avg": [3.5, 0.7],           // [mean, std] for support
  "significance_avg": [4.2, 0.4],      // [mean, std] for significance
  
  // Word counts
  "wc_summary": "150;200;180",          // Summary word counts
  "wc_strengths_and_weaknesses": "300;250;400", // S&W word counts
  "wc_questions": "50;75;60",           // Questions word counts
  "wc_review": "500;525;640",           // Total review word counts
  "wc_summary_avg": [176.7, 25.2],     // [mean, std] for summaries
  "wc_review_avg": [555.0, 72.1],      // [mean, std] for reviews
  
  // Correlations
  "corr_rating_confidence": 0.65        // Rating-confidence correlation
}
```

### Citation Data
```json
{
  "gs_citation": 42,                    // Google Scholar citation count
  "gs_cited_by_link": "https://scholar.google.com/...", // Citations URL
  "gs_version_total": 3                 // Number of versions
}
```

### Keywords
```json
{
  "keywords": "machine learning;neural networks;deep learning" // Semicolon-separated
}
```

## Processing Pipeline

### 1. Initialization Phase
```python
def __init__(self, config: ImporterConfig = None, database_url: str = None):
    # Load configuration
    # Initialize logging system
    # Create database engine and session
    # Create performance indexes
    # Initialize statistics tracking
```

### 2. Main Processing Loop
```python
def transform_paperlists_data(self, paperlists_json: List[Dict]):
    for paper_data in paperlists_json:
        # Check if paper already exists (skip duplicates)
        # Process single paper with comprehensive checks
        # Commit immediately after each paper
        # Track processing statistics and timing
        # Log progress every batch_size papers
```

### 3. Single Paper Processing
```python
def process_single_paper_with_checks(self, data: Dict):
    # 1. Create Paper entity with track/conference info
    # 2. Process Authors and their Affiliations
    # 3. Process Keywords
    # 4. Process Reviews (individual + statistics)
    # 5. Process Citations
```

### 4. Entity Creation with Existence Checks

Each entity type has dedicated creation methods with comprehensive existence checking:

#### Papers
```python
def create_paper_with_checks(self, data: Dict) -> Optional[Paper]:
    # Extract conference and track information
    # Create or get existing track
    # Create paper with all metadata
```

#### Authors
```python
def get_or_create_author_with_checks(self, name: str, **kwargs) -> Optional[Author]:
    # Try to find by ORCID first (most reliable)
    # Try to find by OpenReview profile
    # Generate unique author ID if creating new
    # Handle ID collisions with counter suffix
```

#### Institutions
```python
def get_or_create_institution_with_checks(self, name: str, normalized_name: str,
                                        country: Country, **kwargs) -> Optional[Institution]:
    # Check for existing institution by normalized_name + country + campus
    # Create new institution with all metadata
    # Extract domain from website URL
```

#### Countries
```python
def get_or_create_country_with_checks(self, name: str) -> Optional[Country]:
    # Simple existence check by name
    # Create if not exists
```

### 5. Relationship Processing

#### Author-Paper Relationships
```python
def process_authors_and_affiliations_with_checks(self, paper: Paper, data: Dict):
    # Parse all semicolon-separated author fields
    # Create author entities with existence checks
    # Create paper-author relationships with ordering
    # Process affiliations for each author
```

#### Author-Institution Affiliations
```python
def process_author_affiliations_with_checks(self, author: Author, aff_indices: str,
                                           institution_map: Dict[str, Institution],
                                           position: str, email_domain: str):
    # Handle multi-affiliations (+ separated indices)
    # Create affiliation records with position/department info
    # Mark primary affiliation
```

### 6. Data Parsing Utilities

The script includes robust parsing utilities for the semicolon-separated format:

```python
def parse_semicolon_field(self, field: str) -> List[str]:
    # Split on semicolons and strip whitespace
    
def parse_numeric_field(self, field: str) -> List[int]:
    # Parse semicolon-separated integers
    
def safe_get(self, lst: List, index: int, default=None):
    # Safely access list elements with bounds checking
```

### 7. Conference and Track Classification

```python
def extract_conference_name(self, paper_data: Dict) -> str:
    # Extract from bibtex or site URL
    # Support for ICML, NeurIPS, ICLR, etc.
    
def classify_track(self, track_name: str) -> Tuple[str, str]:
    # Classify as main, workshop, tutorial, demo, etc.
    # Generate full track names
```

## Error Handling and Validation

### Comprehensive Existence Checking
- **Papers**: Check by ID before processing
- **Authors**: Check by ORCID, then OpenReview ID
- **Institutions**: Check by normalized name + country + campus
- **Countries**: Check by name
- **Relationships**: Check all junction tables for duplicates

### Transaction Management
- **Individual commits**: Each paper is committed separately
- **Rollback on error**: Failed papers don't affect others
- **Duplicate handling**: Skip existing papers gracefully

### Data Validation
- **Required fields**: Validate essential data is present
- **Format validation**: Check URL formats, numeric ranges
- **Constraint enforcement**: Respect database constraints
- **Referential integrity**: Ensure all foreign keys are valid

## Performance Optimizations

### Database Indexes
```python
def _ensure_indexes(self):
    # Create performance indexes for common lookups
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_institution_normalized_lookup ON institutions (normalized_name)",
        "CREATE INDEX IF NOT EXISTS idx_author_orcid_lookup ON authors (orcid)",
        "CREATE INDEX IF NOT EXISTS idx_paper_id_lookup ON papers (id)",
        # ... more indexes
    ]
```

### Batch Processing
- **Configurable batch size**: Default 10 papers per batch
- **Progress logging**: Regular progress updates
- **Memory management**: Flush sessions regularly
- **Time estimation**: Calculate remaining processing time

### Query Optimization
- **Compound indexes**: Multi-column indexes for complex queries
- **Selective loading**: Only load necessary fields
- **Existence checks**: Fast lookups before creation
- **Session configuration**: Optimized SQLAlchemy settings

## Logging and Monitoring

### Comprehensive Logging System
```python
# Multiple log levels and files
self.logger = get_logger("paperlist_importer", self.config.log_directory)

# Operation tracking
self.logger.start_operation("processing_paper", paper_id=paper_id)
self.logger.end_operation("processing_paper", success=True)

# Performance monitoring
self.logger.log_data_stats("batch_completed", batch_size, duration=batch_time)
```

### Statistics Tracking
```python
self.stats = {
    'papers_processed': 0,
    'papers_skipped': 0,
    'papers_failed': 0,
    'authors_created': 0,
    'institutions_created': 0,
    'countries_created': 0,
    'start_time': time.time()
}
```

### Post-Import Verification
```python
def verify_import_success(self, original_data: List[Dict], expected_count: int):
    # Random sampling verification
    # Data integrity checks
    # Statistics comparison
    # Database consistency validation
```

## CLI Interface

### Single File Processing

#### Command Line Arguments
```bash
python paperlist_importer.py data.json [options]

Required:
  data.json                 Path to JSON file containing paperlist data

Optional:
  --database, -d DATABASE   Path to SQLite database file
  --config, -c CONFIG       Path to configuration JSON file
  --log-level, -l LEVEL     Logging level (DEBUG/INFO/WARNING/ERROR)
```

#### Usage Examples
```bash
# Basic usage
python paperlist_importer.py icml2024.json

# Custom database
python paperlist_importer.py icml2024.json --database icml2024.db

# Debug logging
python paperlist_importer.py icml2024.json --log-level DEBUG

# All options
python paperlist_importer.py icml2024.json --database custom.db --log-level DEBUG
```

### Batch Processing (Multiple Files)

#### Command Line Arguments
```bash
python batch_importer.py directory [options]

Required:
  directory                 Directory to search for JSON files (recursive)

Optional:
  --output, -o OUTPUT       Output directory for databases and logs
  --config, -c CONFIG       Path to configuration JSON file
  --parallel, -p            Process files in parallel
  --max-workers, -w N       Maximum number of parallel workers (default: 2)
  --log-level, -l LEVEL     Logging level (DEBUG/INFO/WARNING/ERROR)
```

#### Batch Processing Features
- **Recursive Discovery**: Automatically finds all JSON files in subdirectories
- **Shared Database**: Combines all JSON files into a single database (configurable)
- **Isolated Logging**: Each file gets its own log directory with detailed logs
- **Parallel Processing**: Optional parallel processing for smaller files
- **Progress Tracking**: Real-time progress across all files
- **Error Isolation**: Failed files don't stop processing of other files
- **Smart Naming**: Output files named based on source JSON file paths

#### Batch Usage Examples
```bash
# Process all JSON files in a directory
python batch_importer.py /path/to/conference/data

# Process with custom output directory
python batch_importer.py /path/to/conference/data --output /path/to/processed

# Process in parallel (for smaller files)
python batch_importer.py /path/to/conference/data --parallel --max-workers 4

# Custom configuration
python batch_importer.py /path/to/conference/data --config custom_config.json

# Debug mode for troubleshooting
python batch_importer.py /path/to/conference/data --log-level DEBUG
```

#### Batch Output Structure
```
output_directory/
├── icml2024.db                    # Database for icml2024.json
├── neurips2024.db                 # Database for neurips2024.json
├── logs/
│   ├── icml2024/                  # Logs for icml2024.json processing
│   │   ├── paperlist_importer_main.log
│   │   ├── paperlist_importer_main_errors.log
│   │   └── paperlist_importer_main_performance.log
│   └── neurips2024/               # Logs for neurips2024.json processing
│       ├── paperlist_importer_main.log
│       ├── paperlist_importer_main_errors.log
│       └── paperlist_importer_main_performance.log
└── batch_importer_20241230_032000.log  # Main batch processing log
```

## Configuration Customization

### Database Settings
```python
# Custom database location
config.database_url = "sqlite:///custom_papers.db"

# Session configuration
config.session_autoflush = True
config.session_expire_on_commit = False
```

### Processing Settings
```python
# Batch processing
config.batch_size = 20  # Process 20 papers per batch

# Verification
config.verification_sample_size = 50  # Verify 50 random papers

# Author ID generation
config.max_author_id_attempts = 500  # Try 500 variations before timestamp
```

### Conference Support
```python
# Add new conferences
config.conference_full_names["CUSTOM_CONF"] = "My Custom Conference"

# Track classifications
config.track_classifications["special_track"] = "workshop"
```

## Output and Results

### Database Creation
- **SQLite database**: Created at specified location
- **Full schema**: All tables and relationships created
- **Indexes**: Performance indexes automatically created
- **Constraints**: All integrity constraints enforced

### Logging Output
- **Main log**: `paperlist_importer_main.log`
- **Error log**: `paperlist_importer_main_errors.log`
- **Performance log**: `paperlist_importer_main_performance.log`

### Statistics Report
```
📊 Final Database Statistics:
  Papers: 1,234
  Authors: 5,678
  Institutions: 890
  Countries: 45
  Keywords: 2,345
  Reviews: 3,456
  Citations: 1,234

🌍 Top 5 Countries by Institution Count:
  United States: 234 institutions
  China: 123 institutions
  United Kingdom: 89 institutions

⚡ Performance Metrics:
  Total processing time: 45.67 seconds
  Papers processed per second: 27.03
  Average time per paper: 0.037s
```

## Troubleshooting

### Common Issues

1. **Memory Issues**: Reduce batch_size in configuration
2. **Slow Performance**: Check database indexes, reduce verification_sample_size
3. **Duplicate Errors**: Enable duplicate checking, verify input data quality
4. **Missing Dependencies**: Install required packages from requirements.txt

### Debug Mode
```bash
python paperlist_importer.py data.json --log-level DEBUG
```

This provides detailed logging of:
- Individual paper processing steps
- Database query execution
- Error stack traces
- Performance timing for each operation

### Data Quality Issues
- **Missing required fields**: Papers with missing IDs are skipped
- **Invalid affiliations**: Institutions with missing countries default to "Unknown"
- **Malformed data**: Robust parsing handles missing or malformed fields gracefully
