![Lossfunk India@ML Logo](./lossfunk-indiaml.png)
# IndiaML Tracker Documentation

## Project Overview

The IndiaML Tracker was developed to highlight India's contributions to the global machine learning research landscape. It systematically collects, processes, and analyzes research papers from major AI conferences, focusing on identifying and tracking author affiliations with Indian institutions.

## Architecture Diagram

![IndiaML Architecture Diagram](./indiaml-architecture.svg)

## Project Structure (Pipeline code is relative to indiaml)

```
indiaml/
├── __init__.py
├── main.py
├── pipeline/
│   ├── __init__.py
│   ├── affiliation_checker.py
│   ├── process_venue.py
│   ├── process_authors.py
│   ├── process_paper_author_mapping.py
│   ├── patch_unk_cc2.py
│   ├── patch_unk_cc3.py
│   ├── patch_unk_cc4.py
│   └── patch_unk_cc5.py
├── config/
│   ├── db_config.py
│   ├── venues_config.py
│   ├── name2cc.py
│   └── d2cc.py
├── models/
│   ├── models.py
│   └── dto.py
├── venue_adapters/
│   ├── adapter_factory.py
│   ├── base_adapter.py
│   ├── neurips_adapter.py
│   ├── icml_adapter.py
│   └── icai_adapter.py
├── venue/
│   └── venudao.py
├── analytics/
│   └── analytics.py
└── tests/
    └── test_affiliation_checker.py
```

## Core Components

### 1. Data Models (`indiaml/models/`)

The system uses two types of data models:

#### Database Models (`indiaml/models/models.py`)

SQLAlchemy ORM classes that represent the database schema:

```python
# Key database entities:
class VenueInfo(Base):     # Conference venue details
class Paper(Base):         # Research paper information
class Author(Base):        # Author details 
class PaperAuthor(Base):   # Many-to-many mapping with affiliation data
```

#### Data Transfer Objects (`indiaml/models/dto.py`)

Lightweight objects for transferring data between components:

```python
@dataclass
class AuthorDTO:
    name: str
    email: Optional[str] = None
    # Other author fields...

@dataclass
class PaperDTO:
    id: str
    title: str
    # Other paper fields...
    authors: List[AuthorDTO]
```

### 2. Pipeline Components (`indiaml/pipeline/`)

The data processing pipeline consists of several sequential steps:

#### Paper Metadata Processing (`indiaml/pipeline/process_venue.py`)

Fetches and stores paper metadata from conference venues:

```python
def main_flow(configs: List[VenueConfig], only_accepted: bool = True, cache_dir: str = "cache"):
    """
    Orchestrate the processing of multiple venues:
    - Fetch papers
    - Store metadata
    """
    # Implementation...
```

#### Author Processing (`indiaml/pipeline/process_authors.py`)

Processes authors from stored papers:

```python
def process_authors():
    """Process authors from stored papers and save them to the database."""
    # Implementation...
```

#### Affiliation Checking (`indiaml/pipeline/affiliation_checker.py`)

Core component that resolves author affiliations based on publication date:

```python
class AffiliationChecker:
    def resolve_affiliation(self, affiliation_history: List[Dict[str, Any]], 
                            paper_date: datetime) -> Optional[Dict[str, Any]]:
        """
        Determine the author's affiliation at the time of the paper's publication.
        """
        # Implementation...
```

#### Paper-Author Mapping (`indiaml/pipeline/process_paper_author_mapping.py`)

Links papers to authors with the correct affiliation information:

```python
def create_paper_authors():
    """
    Populate the PaperAuthor table with paper-author associations and affiliation details.
    """
    # Implementation...
```

#### Country Code Resolution (`indiaml/pipeline/patch_unk_cc*.py`)

Multiple scripts for resolving unknown country codes:

- `indiaml/pipeline/patch_unk_cc2.py`: Uses domain-based inference
- `indiaml/pipeline/patch_unk_cc3.py`: Uses name-based mapping
- `indiaml/pipeline/patch_unk_cc4.py`: Additional name-based mapping
- `indiaml/pipeline/patch_unk_cc5.py`: Advanced resolution using LLM-based content analysis

### 3. Venue Adapters (`indiaml/venue_adapters/`)

The adapter pattern allows handling different data sources uniformly:

#### Base Adapter (`indiaml/venue_adapters/base_adapter.py`)

Abstract base class for venue-specific adapters:

```python
class BaseAdapter(ABC):
    @abstractmethod
    def fetch_papers(self) -> List[PaperRecord]:
        """Fetches papers from the provider."""
        pass
        
    @abstractmethod
    def determine_status(self, venue_group: openreview.Group, venueid: str) -> str:
        """Determines the submission status based on venue-specific logic."""
        pass
        
    @abstractmethod
    def fetch_authors(self, author_ids: List[str]) -> List[AuthorDTO]:
        """Fetches author details for the given author IDs."""
        pass
```

#### Conference-Specific Adapters

- `indiaml/venue_adapters/neurips_adapter.py`: Implementation for NeurIPS
- `indiaml/venue_adapters/icml_adapter.py`: Implementation for ICML
- `indiaml/venue_adapters/icai_adapter.py`: Implementation for ICAI

#### Adapter Factory (`indiaml/venue_adapters/adapter_factory.py`)

Factory pattern for creating appropriate adapters:

```python
def get_adapter(config) -> BaseAdapter:
    """Factory function to get the appropriate adapter instance based on the config."""
    # Implementation...
```

### 4. Database Access Layer (`indiaml/venue/venudao.py`)

Repository pattern implementation for database operations:

```python
class VenueDB:
    """Data Access Layer using SQLAlchemy ORM."""
    
    def store_papers(self, paper_dtos: List[PaperDTO]):
        # Implementation...
        
    def get_or_create_author(self, author_dto: AuthorDTO) -> Author:
        # Implementation...
        
    def resolve_affiliation(self, author: Author, paper_date: datetime) -> Optional[Dict]:
        # Implementation...
```

### 5. Configuration (`indiaml/config/`)

Various configuration files:

- `indiaml/config/venues_config.py`: Conference venue configurations
- `indiaml/config/db_config.py`: Database configuration
- `indiaml/config/name2cc.py`: Institution name to country code mappings
- `indiaml/config/d2cc.py`: Domain to country code mappings

### 6. Analytics (`indiaml/analytics/analytics.py`)

Generates analytics from the processed data:

```python
def generate_papers_json(output_path='papers_output.json'):
    """Generates a JSON file with paper information and author affiliations."""
    # Implementation...
```

### 7. Tests (`indiaml/tests/`)

Unit tests for components:

- `indiaml/tests/test_affiliation_checker.py`: Tests for the AffiliationChecker

## Pipeline Execution Flow

To build a complete dataset, execute these steps in sequence:

```bash
# 1. Fetch and store paper metadata
python -m indiaml.pipeline.process_venue

# 2. Process author information
python -m indiaml.pipeline.process_authors

# 3. Create paper-author mappings with affiliations
python -m indiaml.pipeline.process_paper_author_mapping

# 4. Resolve unknown country codes (run in sequence)
python -m indiaml.pipeline.patch_unk_cc2
python -m indiaml.pipeline.patch_unk_cc3
python -m indiaml.pipeline.patch_unk_cc4

# 5. Advanced country resolution (optional, requires API key)
python -m indiaml.pipeline.patch_unk_cc5

# 6. Generate analytics output
python -m indiaml.analytics.analytics
```

## Environment Setup

### Prerequisites
1. Python 3.8+
2. Access to OpenReview API
3. SQLite (for database storage)
4. Required Python packages (install via `pip install -r requirements.txt`):
   - sqlalchemy
   - openreview-py
   - pydantic
   - requests
   - pymupdf4llm
   - python-dotenv

### Configuration

1. Create a `.env` file in the project root:
   ```
   OPENROUTER_API_KEY=your_api_key_here  # For LLM-based affiliation resolution
   ```

2. Configure venues in `indiaml/config/venues_config.py`:
   ```python
   VENUE_CONFIGS = [
       VenueConfig(
           conference="NeurIPS",
           year=2024,
           track="Conference",
           source_adapter="openreview",
           source_id="NeurIPS.cc/2024/Conference",
           adapter_class="NeurIPSAdapter"
       ),
       # Add more conferences as needed
   ]
   ```

## Adding New Data Sources

To extend the system with new conference sources:

1. **Create a new adapter** in `indiaml/venue_adapters/`:
   ```python
   # indiaml/venue_adapters/new_conference_adapter.py
   from .base_adapter import BaseAdapter
   
   class NewConferenceAdapter(BaseAdapter):
       def fetch_papers(self) -> List[PaperDTO]:
           # Implementation...
           
       def determine_status(self, venue_group, venueid) -> str:
           # Implementation...
           
       def fetch_authors(self, author_ids) -> List[AuthorDTO]:
           # Implementation...
   ```

2. **Update the adapter factory** in `indiaml/venue_adapters/adapter_factory.py`:
   ```python
   adapter_classes = {
       # Existing adapters...
       "NewConferenceAdapter": NewConferenceAdapter,
   }
   ```

3. **Add configuration** in `indiaml/config/venues_config.py`:
   ```python
   VENUE_CONFIGS.append(
       VenueConfig(
           conference="NewConference",
           year=2024,
           track="Conference",
           source_adapter="openreview",  # or other source
           source_id="NewConference.cc/2024/Conference",
           adapter_class="NewConferenceAdapter"
       )
   )
   ```

## Testing

Run the test suite:

```bash
# Run all tests
python -m unittest discover indiaml.tests

# Run specific test
python -m unittest indiaml.tests.test_affiliation_checker
```

## Output

After running the pipeline, results will be available in:
- SQLite database: `venues.db`
- JSON output: `papers_output.json` (generated by `indiaml.analytics.analytics`)

## License

[MIT License](LICENSE)