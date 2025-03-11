# IndiaML Tracker Technical Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Research Landscape and OpenReview](#research-landscape-and-openreview)
3. [System Architecture](#system-architecture)
4. [Design Patterns](#design-patterns)
5. [Data Pipeline](#data-pipeline)
6. [Database Schema](#database-schema)
7. [Modules and Components](#modules-and-components)
8. [Workflows](#workflows)
9. [API Integration](#api-integration)
10. [Analytics Generation](#analytics-generation)
11. [Configuration](#configuration)
12. [Troubleshooting](#troubleshooting)
13. [Future Development](#future-development)

## Architecture Diagram

![IndiaML Architecture](./indiaml-architecture.svg)

## Project Overview

IndiaML Tracker is a data aggregation and analysis system designed to highlight India's contributions to global machine learning research. The project systematically identifies, analyzes, and highlights research papers from top-tier ML conferences that include authors affiliated with Indian institutions.

The system focuses on building a comprehensive database of ML research papers with Indian author affiliations, analyzing institutional patterns, tracking year-over-year growth in India's contributions, and visualizing research collaborations between Indian and international institutions.

## Research Landscape and OpenReview

Understanding the academic research ecosystem, particularly for machine learning conferences, is essential to grasp why the IndiaML Tracker architecture is designed as it is.

### ML Research Conference Structure

Machine learning research follows a rigorous publication cycle:

1. **Conference Calls for Papers**: Top conferences like NeurIPS, ICML, and ICLR release calls for paper submissions.
2. **Submission Process**: Authors submit papers through platforms like OpenReview.
3. **Peer Review**: Papers undergo blind peer review by experts in the field.
4. **Decision and Publication**: Accepted papers are published in conference proceedings.

This cycle creates a structured data source that the IndiaML Tracker leverages.

### OpenReview Platform

OpenReview is a web platform that supports the entire conference reviewing process, making it an ideal primary data source for the IndiaML Tracker:

1. **Standardized API**: OpenReview provides a consistent API that facilitates data extraction.
2. **Structured Metadata**: Paper submissions include standardized metadata such as:
   - Author names and identifiers
   - Institutional affiliations
   - Paper titles and abstracts
   - Submission status (accepted, rejected, withdrawn)
   - PDF links to the full papers

3. **Author Profiles**: OpenReview maintains profiles that link authors across multiple papers and conferences, which helps track researchers' affiliations over time.

4. **Hierarchical Organization**: OpenReview organizes content hierarchically:
   - Conferences (e.g., "NeurIPS.cc")
   - Years (e.g., "2024")
   - Tracks (e.g., "Conference", "Workshop")
   - Submissions (identified by unique IDs)

This structure maps cleanly to the IndiaML Tracker's database schema and architecture.

### Affiliation Challenges

Several factors make tracking author affiliations particularly challenging:

1. **Inconsistent Reporting**: Authors may list their affiliations differently across papers.
2. **Multiple Affiliations**: Researchers often have primary and secondary affiliations.
3. **Temporal Changes**: Researchers change institutions throughout their careers.
4. **Ambiguous Names**: Different institutions may have similar names or abbreviations.

These challenges necessitate the multi-stage affiliation resolution approach used in IndiaML Tracker.

## System Architecture

The IndiaML Tracker follows a modular, pipeline-based architecture:

```
                 +-------------+
                 | Configuration|
                 +-------------+
                        |
                        v
+-------------+   +-------------+   +-------------+
| Data Sources|-->| Adapters    |-->| Pipeline    |
+-------------+   +-------------+   +-------------+
                        |                |
                        v                v
                 +-------------+   +-------------+
                 | Database    |<--| Affiliation |
                 |             |   | Resolution  |
                 +-------------+   +-------------+
                        |
                        v
                 +-------------+
                 | Analytics   |
                 | Generation  |
                 +-------------+
```

### Key Components

1. **Data Sources**: Currently supports OpenReview for conferences like NeurIPS, ICML, and ICAI.
2. **Adapters**: Interfaces with data sources and normalizes data for the pipeline.
3. **Pipeline**: Processes venue data, author information, and paper-author mapping.
4. **Affiliation Resolution**: Multi-stage approach to determine and verify author affiliations.
5. **Database**: SQLite database storing papers, authors, affiliations, and their relationships.
6. **Analytics Generation**: Processes the curated data to produce insights and visualizations.

## Data Pipeline

The data processing pipeline consists of several sequential steps:

### 1. Venue Processing (`process_venue.py`)

- Fetches paper metadata from configured venues (conferences)
- Normalizes and stores basic paper information
- Captures raw author data for further processing

### 2. Author Processing (`process_authors.py`)

- Extracts author information from papers
- Creates or updates author records in the database
- Preserves affiliation history data for later resolution

### 3. Paper-Author Mapping (`process_paper_author_mapping.py`)

- Creates associations between papers and authors
- Determines correct author ordering for each paper
- Begins preliminary affiliation mapping

### 4. Affiliation Resolution (Patch Scripts)

The system employs a multi-stage approach to resolve affiliations:

- **Stage 1** (`patch_unk_cc2.py`): Domain-based resolution using email domain or website
- **Stage 2** (`patch_unk_cc3.py`): Name-based resolution using institution name
- **Stage 3** (`patch_unk_cc4.py`): Additional name-based resolution with expanded mapping
- **Stage 4** (`patch_unk_cc5.py`): LLM-based resolution for difficult cases

### 5. Analytics Generation (`analytics.py`)

- Compiles the processed data into structured JSON
- Generates analysis of institutional contributions
- Prepares data for visualization and reporting

## Database Schema

The system uses SQLalchemy ORM with the following core models:

### VenueInfo

Stores information about research venues:

```python
class VenueInfo(Base):
    __tablename__ = 'venue_infos'
    __table_args__ = (UniqueConstraint('conference', 'year', 'track', name='uix_conference_year_track'),)
    
    id = Column(Integer, primary_key=True)
    conference = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    track = Column(String, nullable=False)
    
    papers = relationship("Paper", back_populates="venue_info", cascade="all, delete-orphan")
```

### Paper

Stores research paper details:

```python
class Paper(Base):
    __tablename__ = 'papers'
    
    id = Column(String, primary_key=True)  # e.g., OpenReview ID
    venue_info_id = Column(Integer, ForeignKey('venue_infos.id'), nullable=False)
    
    title = Column(String, nullable=False)
    status = Column(String)
    pdf_url = Column(String)
    pdf_path = Column(String)
    pdate = Column(DateTime)
    odate = Column(DateTime)
    raw_authors = Column(JSON, nullable=True)
    
    venue_info = relationship("VenueInfo", back_populates="papers")
    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")
```

### Author

Stores author information:

```python
class Author(Base):
    __tablename__ = 'authors'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=False, nullable=True)
    openreview_id = Column(String, unique=True, nullable=True)
    orcid = Column(String, nullable=True)
    google_scholar_link = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    homepage = Column(String, nullable=True)
    affiliation_history = Column(JSON, nullable=True)

    papers = relationship("PaperAuthor", back_populates="author", cascade="all, delete-orphan")
```

### PaperAuthor

Association table connecting papers and authors:

```python
class PaperAuthor(Base):
    __tablename__ = 'paper_authors'
    
    paper_id = Column(String, ForeignKey('papers.id'), primary_key=True)
    author_id = Column(Integer, ForeignKey('authors.id'), primary_key=True)
    position = Column(Integer, nullable=False)
    
    # Affiliation details
    affiliation_name = Column(String, nullable=True)
    affiliation_domain = Column(String, nullable=True)
    affiliation_state_province = Column(String, nullable=True)
    affiliation_country = Column(String, nullable=True)
    
    paper = relationship("Paper", back_populates="authors")
    author = relationship("Author", back_populates="papers")
```

## Design Patterns

The IndiaML Tracker employs several established software design patterns to ensure maintainability, extensibility, and separation of concerns:

### Adapter Pattern

**Implementation**: `venue_adapters/base_adapter.py`, `venue_adapters/neurips_adapter.py`, etc.

The Adapter pattern is used to transform data from different sources (like OpenReview) into a consistent format for the system to process. This is particularly valuable because:

1. **Different Data Source Structures**: Each conference platform may structure its data differently.
2. **API Variations**: API endpoints and parameters can vary between sources.
3. **Extensibility**: New data sources can be added without modifying existing code.

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
```

By defining a common interface, the system can work with any data source as long as it provides the required information through the adapter.

### Factory Pattern

**Implementation**: `venue_adapters/adapter_factory.py`

The Factory pattern is used to create appropriate adapter instances based on configuration:

```python
def get_adapter(config) -> BaseAdapter:
    """Factory function to get the appropriate adapter instance based on the config."""
    adapter_classes = {
        "NeurIPSAdapter": NeurIPSAdapter,
        "ICMLAdapter": ICMLAdapter,
        "ICAIAdapter": ICAIAdapter
    }
    
    adapter_class = adapter_classes.get(config.adapter_class)
    if not adapter_class:
        raise ValueError(f"Unknown adapter class: {config.adapter_class}")
    
    return adapter_class(config)
```

This pattern was chosen because:

1. **Decoupling**: The client code (pipeline) doesn't need to know the details of adapter creation.
2. **Configuration-Driven**: Adapters can be selected through configuration without code changes.
3. **Centralized Creation Logic**: All adapter instantiation logic is in one place, making it easier to manage.

### Repository Pattern

**Implementation**: `venue/venudao.py`

The Repository pattern abstracts data access operations, providing a clean separation between business logic and database operations:

```python
class VenueDB:
    """DAL using SQLAlchemy ORM."""

    def __init__(self):
        self.session = SessionLocal()

    def get_or_create_author(self, author_dto: AuthorDTO) -> Author:
        # Implementation
        pass

    def store_papers(self, paper_dtos: List[PaperDTO]):
        # Implementation
        pass
```

Benefits of this approach include:

1. **Encapsulation**: Database operations are encapsulated within repository methods.
2. **Testability**: Business logic can be tested without touching the database by mocking the repository.
3. **Maintainability**: Changes to the database schema or ORM only require updates to the repository.

### Data Transfer Objects (DTO)

**Implementation**: `models/dto.py`

DTOs are used to transfer data between components without exposing internal details:

```python
@dataclass
class AuthorDTO:
    name: str
    email: Optional[str] = None
    openreview_id: Optional[str] = None
    # Additional fields
```

This pattern was chosen because:

1. **Loose Coupling**: Components can exchange data without being tightly coupled.
2. **Selective Exposure**: Only necessary data is transferred between components.
3. **Validation**: DTOs can include validation logic to ensure data integrity.

### Pipeline Pattern

**Implementation**: The sequence of processing scripts in the `pipeline` directory.

The Pipeline pattern structures data processing as a series of discrete stages, where each stage's output becomes the input for the next stage:

1. Venue Processing → Author Processing → Paper-Author Mapping → Affiliation Resolution

This pattern was chosen for:

1. **Modularity**: Each step has a clear, focused responsibility.
2. **Failure Isolation**: Issues in one stage don't necessarily affect others.
3. **Parallelization Potential**: Stages can potentially run in parallel for improved performance.
4. **Restart Capability**: Processing can be resumed from any stage in case of failures.

## Modules and Components

### Venue Adapters

Adapters transform data from different sources into a standardized format for the pipeline. Currently supported:

- `NeurIPSAdapter`: For NeurIPS conference data
- `ICMLAdapter`: For ICML conference data
- `ICAIAdapter`: For ICAI conference data

New adapters can be added by:

1. Subclassing `BaseAdapter` or another existing adapter
2. Implementing required methods (fetch_papers, determine_status, fetch_authors)
3. Registering in the adapter factory

### Affiliation Checker

The `AffiliationChecker` class in `pipeline/affiliation_checker.py` determines the correct affiliation for an author at the time a paper was published:

```python
def resolve_affiliation(self, affiliation_history: List[Dict[str, Any]], paper_date: datetime) -> Optional[Dict[str, Any]]:
    """
    Determine the author's affiliation at the time of the paper's publication.
    """
    # Algorithm determines correct affiliation based on dates
```

### Configuration

Configuration files include:
- `venues_config.py`: Defines venues/conferences to track
- `name2cc.py`: Maps institution names to country codes
- `d2cc.py`: Maps domains to country codes
- `db_config.py`: Database connection settings

### DTO (Data Transfer Objects)

The system uses DTOs to pass data between different components:

- `AuthorDTO`: Represents author information
- `PaperDTO`: Represents paper details

## Workflows

### Complete Pipeline Execution

To run the complete pipeline:

```bash
# Process venues and papers
python -m indiaml.pipeline.process_venue

# Process author information
python -m indiaml.pipeline.process_authors

# Link papers and authors, initial affiliation mapping
python -m indiaml.pipeline.process_paper_author_mapping

# Multi-stage affiliation resolution
python -m indiaml.pipeline.patch_unk_cc2
python -m indiaml.pipeline.patch_unk_cc3
python -m indiaml.pipeline.patch_unk_cc4
python -m indiaml.pipeline.patch_unk_cc5

# Generate analytics
python -m indiaml.analytics.analytics
```

### Adding a New Data Source

To add a new data source:

1. Create a new adapter class in `venue_adapters/`
2. Register the adapter in `adapter_factory.py`
3. Add configuration entries in `venues_config.py`
4. Update any necessary affiliation mappings in `name2cc.py` and `d2cc.py`

## API Integration

### OpenReview API

The system uses the OpenReview API to fetch papers and author information:

```python
from openreview import OpenReviewClient, Profile

# Initialize client
client = OpenReviewClient(baseurl="https://api2.openreview.net")

# Fetch papers
invitation = f"{source_id}/-/Submission"
notes = client.get_all_notes(invitation=invitation)

# Fetch author profiles
profiles = openreview.tools.get_profiles(
    client,
    ids_or_emails=author_ids,
    with_publications=False,
    with_relations=False
)
```

### LLM Integration

For advanced affiliation resolution, the system can use LLMs (e.g., Claude) via the OpenRouter API:

```python
client = openai.OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=messages,
    max_tokens=4096,
    temperature=0.1
)
```

## Analytics Generation

The analytics module processes the database to generate structured outputs:

```python
def generate_papers_json(output_path='papers_output.json'):
    # Query all papers with related data
    papers = session.query(Paper).options(
        joinedload(Paper.venue_info),
        joinedload(Paper.authors).joinedload(PaperAuthor.author)
    ).all()

    # Transform into structured output
    output_data = []
    for paper in papers:
        # Build conference information
        conference = ConferenceSchema(...)
        # Build authors list
        authors = [...]
        # Create paper entry
        paper_entry = PaperSchema(...)
        output_data.append(paper_entry.model_dump())
    
    # Write to JSON file
    with open(output_path, 'w') as f:
        f.write(response.model_dump_json(indent=2))
```

## Configuration

### Environment Variables

Required environment variables:
- `OPENROUTER_API_KEY`: API key for OpenRouter LLM access (for advanced affiliation resolution)

### Configuration Files

- `venues_config.py`: Contains VenueConfig objects for each venue to track
- `name2cc.py`: Maps institution names to country codes
- `d2cc.py`: Maps domains to country codes
- `db_config.py`: Database connection configuration

Example venue configuration:
```python
VenueConfig(
    conference="NeurIPS",
    year=2024,
    track="Conference",
    source_adapter="openreview",
    source_id="NeurIPS.cc/2024/Conference",
    adapter_class="NeurIPSAdapter"
)
```

## Troubleshooting

### Common Issues

1. **Unknown Affiliations**: When the system cannot determine an author's affiliation, it sets the affiliation_country to "UNK". To address:
   - Add entries to name2cc.py or d2cc.py
   - Run the patch scripts again
   - Use the LLM-based resolution (patch_unk_cc5.py)

2. **API Rate Limits**: OpenReview API may enforce rate limits. Implement retry logic with exponential backoff.

3. **PDF Processing Issues**: When extracting information from PDFs:
   - Ensure pymupdf4llm is correctly installed
   - Implement fallback mechanisms for poorly formatted PDFs

### Logging

The system uses Python's logging module. Logs are output to stdout by default:

```python
# Setup Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
```

## Future Development

### Planned Enhancements

1. **Improved Affiliation Resolution**:
   - Enhanced heuristics for domain-based resolution
   - Improved country code mapping

1. **Data Visualization**:
- Interactive dashboards for trends and metrics
- Collaboration network graphs

1. **Quality Improvements**:
   - Expanded test coverage
   - Enhanced validation of data integrity
   - Automated data quality checks

1. **Additional Data Sources**:
   - arXiv (ML/AI categories)
   - ACL Anthology
   - IEEE Xplore
   - ACM Digital Library

1. **API Development**:
   - REST API for accessing the dataset

### Contributing

Please refer to CONTRIBUTING.md for detailed guidelines on contributing to the project.