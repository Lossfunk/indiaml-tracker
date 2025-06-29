# Paperlist Importer

A configurable tool for importing paperlist JSON data into SQLite databases with comprehensive logging and CLI support.

## Features

- ✅ **CLI Support**: JSON file path as required argument
- ✅ **Configurable**: All constants moved to configuration file
- ✅ **Comprehensive Conference Support**: 25+ conferences supported
- ✅ **Flexible Database**: Configurable database path
- ✅ **Enhanced Logging**: Detailed logging with configurable levels
- ✅ **Backward Compatible**: Legacy functions still work

## Usage

### Basic Usage
```bash
python pipeline/paperlist_importer.py data.json
```

### Advanced Usage
```bash
# Custom database
python pipeline/paperlist_importer.py data.json --database custom.db

# Debug logging
python pipeline/paperlist_importer.py data.json --log-level DEBUG

# All options combined
python pipeline/paperlist_importer.py data.json --database custom.db --log-level DEBUG
```

## Configuration

### Default Configuration
The script uses sensible defaults defined in `config.py`:
- Database: `sqlite:///paperlists.db`
- Log directory: `logs`
- Batch size: `10`
- Comprehensive conference mappings for 25+ venues

### Custom Configuration
Modify the `config.py` file to customize settings:

```python
class ImporterConfig(BaseModel):
    # Database settings
    database_url: str = "sqlite:///custom_papers.db"
    
    # Processing settings
    batch_size: int = 5
    verification_sample_size: int = 20
    max_author_id_attempts: int = 500
    top_countries_limit: int = 10
    
    # Add custom conferences
    conference_full_names: Dict[str, str] = {
        # ... existing conferences ...
        "CUSTOM_CONF": "My Custom Conference"
    }
```

## Supported Conferences

The tool supports 25+ major conferences including:

### AI/ML Core
- AAAI, ICML, NeurIPS, ICLR, IJCAI, AISTATS, ACML, AutoML, UAI

### NLP
- ACL, EMNLP, NAACL, COLING, COLM

### Computer Vision
- CVPR, ICCV, ECCV, WACV

### Graphics
- SIGGRAPH, SIGGRAPHASIA

### Robotics
- ICRA, IROS, RSS, CORL

### Data Mining/Web
- KDD, WWW, ACMMM

### Theory
- COLT

## Files

- `config.py` - Configuration classes and settings
- `pipeline/paperlist_importer.py` - Main importer script
- `README.md` - This documentation

## Migration from Hardcoded Version

### Before (Hardcoded)
```python
# Hardcoded values throughout the code
transformer = PaperlistsTransformer("sqlite:///paperlists.db")
main()  # Used hardcoded 'paperlists_data.json'
```

### After (Configurable)
```bash
# CLI with any JSON file
python paperlist_importer.py your_data.json

# Or with custom database
python paperlist_importer.py your_data.json --database your_db.db
```

## Backward Compatibility

The legacy `main_with_custom_file()` function still works but shows a deprecation warning:

```python
# Still works but deprecated
main_with_custom_file("data.json", "custom.db")
```

## Logging

Logs are written to the configured log directory with multiple levels:
- Main log: `paperlist_importer_main.log`
- Error log: `paperlist_importer_main_errors.log`
- Performance log: `paperlist_importer_main_performance.log`

Set log level with `--log-level DEBUG|INFO|WARNING|ERROR`
