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
13. [Testing](#testing)
14. [Future Development](#future-development)

## Architecture Diagram

![IndiaML Architecture](./indiaml-architecture.svg)

## Project Overview

IndiaML Tracker is a data aggregation and analysis system designed to highlight India's contributions to global machine learning research. The project systematically identifies, analyzes, and highlights research papers from top-tier ML conferences that include authors affiliated with Indian institutions.

The system focuses on building a comprehensive database of ML research papers with Indian author affiliations, analyzing institutional patterns, tracking year-over-year growth in India's contributions, and visualizing research collaborations between Indian and international institutions.

### Key Features

- **Multi-source data collection**: Currently focused on OpenReview with extensibility for additional sources
- **Robust affiliation resolution**: Multi-stage approach to accurately determine author affiliations
- **Country code mapping**: Systematic identification of Indian institutions
- **Paper content analysis**: Optional LLM-based extraction of paper summaries
- **Analytics generation**: Structured outputs for visualization and analysis

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
        
    @abstractmethod
    def fetch_authors(self, author_ids: List[str]) -> List[AuthorDTO]:
        """Fetches detailed author information."""
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
    orcid: Optional[str] = None
    google_scholar_link: Optional[str] = None
    dblp: Optional[str] = None
    linkedin: Optional[str] = None
    homepage: Optional[str] = None
    history: Optional[List[Dict]] = None
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

## Data Pipeline

The data processing pipeline consists of several sequential steps:

### 1. Venue Processing (`process_venue.py`)

- Fetches paper metadata from configured venues (conferences)
- Normalizes and stores basic paper information
- Captures raw author data for further processing

```python
def main_flow(configs: List[VenueConfig], only_accepted: bool = True, cache_dir: str = "cache"):
    """
    Orchestrate the processing of multiple venues:
    - Fetch papers
    - Store metadata
    - Assign affiliations
    """
    init_db()
    
    for cfg in configs:
        logger.info(f"Starting processing for venue: {cfg.conference} {cfg.year} {cfg.track}")
        papers = fetch_paper_metadata(cfg)
        if not papers:
            logger.warning(f"No papers fetched for {cfg.source_id}.")
            continue
        
        store_metadata(cfg, papers)
```

### 2. Author Processing (`process_authors.py`)

- Extracts author information from papers
- Creates or updates author records in the database
- Preserves affiliation history data for later resolution

```python
def process_authors():
    """Process authors from stored papers and save them to the database."""
    try:
        with VenueDB() as db:
            session: Session = db.session
            # Fetch all papers with related venue_info using joinedload to optimize queries
            papers: List[Paper] = session.query(Paper).options(
                joinedload(Paper.venue_info)
            ).all()

            logger.info(f"Processing authors for {len(papers)} papers.")

            for paper in papers:
                # Process paper authors
                # ...
    except Exception as e:
        logger.error(f"Error in processing authors: {e}")
```

### 3. Paper-Author Mapping (`process_paper_author_mapping.py`)

- Creates associations between papers and authors
- Determines correct author ordering for each paper
- Begins preliminary affiliation mapping

```python
def create_paper_authors():
    """
    Populate the PaperAuthor table with paper-author associations and affiliation details.
    """
    try:
        with VenueDB() as db:
            session: Session = db.session

            # Initialize AffiliationChecker
            affiliation_checker = AffiliationChecker()

            # Fetch all papers with their venue_info
            papers: List[Paper] = session.query(Paper).options(
                joinedload(Paper.venue_info)
            ).all()

            logger.info(f"Found {len(papers)} papers in the database.")

            for paper in papers:
                # Process paper authors
                # ...
    except Exception as e:
        logger.error(f"An error occurred while creating PaperAuthor associations: {e}")
```

### 4. Affiliation Resolution (Patch Scripts)

The system employs a multi-stage approach to resolve affiliations:

#### Stage 1: Domain-based Resolution (`patch_unk_cc2.py`)
- Uses email domains or website domains to determine country
- Leverages the `d2cc.py` mapping file

```python
for record in results:
    domain = record.affiliation_domain.lower() if record.affiliation_domain else ""
    match = ccTLD_pattern.search(domain)
    if match:
        country_code = match.group(1).upper()
    else:
        # Use the predefined mapping
        main_domain = domain.split('.')[-2] + '.' + domain.split('.')[-1] if '.' in domain else domain
        country_code = domain_to_cc.get(main_domain, "UNK")
    
    # Update the country code if known
    if country_code != "UNK":
        record.affiliation_country = country_code
```

#### Stage 2: Name-based Resolution (`patch_unk_cc3.py`)
- Uses institution names to determine country
- Leverages the `name2cc.py` mapping file

```python
for record in results:
    name = record.affiliation_name
    country_code = name_to_cc.get(name, "UNK")  # Lookup the name-to-CC mapping

    # Update the country code if a mapping is found
    if country_code != "UNK":
        record.affiliation_country = country_code
```

#### Stage 3: Additional Name-based Resolution (`patch_unk_cc4.py`)
- Similar to Stage 2 but with expanded mapping

#### Stage 4: LLM-based Resolution (`patch_unk_cc5.py`)
- Uses LLMs to extract affiliation details from paper PDFs
- Processes papers with unknown affiliations

```python
def process_paper_authors():
    """
    Main function to process PaperAuthor entries with unknown affiliations.
    """
    paper_authors = get_paper_authors_with_unknown_affiliation()

    # Group PaperAuthors by Paper to minimize PDF downloads
    papers_dict = {}
    for pa in paper_authors:
        paper = pa.paper
        if paper.id not in papers_dict:
            papers_dict[paper.id] = {"paper": paper, "authors": []}
        papers_dict[paper.id]["authors"].append(pa)

    logger.info(f"Processing {len(papers_dict)} papers with unknown author affiliations.")

    for paper_id, data in papers_dict.items():
        # Download PDF, extract text, use LLM to determine affiliations
        # ...
```

### 5. Analytics Generation (`analytics.py`, `generate_final_jsons.py`, `generate_summaries.py`)

- Compiles the processed data into structured JSON
- Generates analysis of institutional contributions
- Creates paper summaries using LLM processing of paper content
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
    conference = Column(String, nullable=False)  # Conference name (e.g., "NeurIPS")
    year = Column(Integer, nullable=False)       # Conference year (e.g., 2024)
    track = Column(String, nullable=False)       # Conference track (e.g., "Conference")
    
    papers = relationship("Paper", back_populates="venue_info", cascade="all, delete-orphan")
```

### Paper

Stores research paper details:

```python
class Paper(Base):
    __tablename__ = 'papers'
    
    id = Column(String, primary_key=True)  # e.g., OpenReview ID
    venue_info_id = Column(Integer, ForeignKey('venue_infos.id'), nullable=False)
    
    title = Column(String, nullable=False)  # Paper title
    status = Column(String)                 # Status (e.g., "accepted", "rejected")
    pdf_url = Column(String)                # URL to the PDF
    pdf_path = Column(String)               # Local path if PDF is cached
    pdate = Column(DateTime)                # Publication date
    odate = Column(DateTime)                # Online date
    raw_authors = Column(JSON, nullable=True)  # Raw author data as JSON
    
    # Relationships
    venue_info = relationship("VenueInfo", back_populates="papers")
    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")
```

### Author

Stores author information:

```python
class Author(Base):
    __tablename__ = 'authors'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)       # Author's full name
    email = Column(String, unique=False, nullable=True)  # Author's email
    openreview_id = Column(String, unique=True, nullable=True)  # e.g. "~John_Smith1"
    orcid = Column(String, nullable=True)            # ORCID identifier
    google_scholar_link = Column(String, nullable=True)  # Google Scholar profile
    linkedin = Column(String, nullable=True)         # LinkedIn profile
    homepage = Column(String, nullable=True)         # Personal/academic homepage
    affiliation_history = Column(JSON, nullable=True)  # History of affiliations as JSON

    papers = relationship("PaperAuthor", back_populates="author", cascade="all, delete-orphan")
```

### PaperAuthor

Association table connecting papers and authors:

```python
class PaperAuthor(Base):
    """
    Association table linking a Paper to an Author, including the
    'position' (i.e., ordering) of the author on that paper and affiliation details.
    """
    __tablename__ = 'paper_authors'
    
    paper_id = Column(String, ForeignKey('papers.id'), primary_key=True)
    author_id = Column(Integer, ForeignKey('authors.id'), primary_key=True)
    position = Column(Integer, nullable=False)  # Author position in paper
    
    # Affiliation details
    affiliation_name = Column(String, nullable=True)  # Institution name
    affiliation_domain = Column(String, nullable=True)  # Institution domain
    affiliation_state_province = Column(String, nullable=True)  # State/province
    affiliation_country = Column(String, nullable=True)  # Country code (e.g., "IN" for India)
    
    paper = relationship("Paper", back_populates="authors")
    author = relationship("Author", back_populates="papers")
```

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
    
    :param affiliation_history: List of affiliation records.
    :param paper_date: Publication date of the paper.
    :return: A dictionary containing affiliation details or None if not found.
    """
    if not affiliation_history:
        logger.debug("No affiliation history provided.")
        return None

    for record in affiliation_history:
        # Extract dates and affiliation details
        start_year = record.get('start')
        end_year = record.get('end')
        institution = record.get('institution', {})
        
        # Convert years to datetime objects for comparison
        start_date = datetime(start_year, 1, 1) if start_year else datetime.min
        end_date = datetime(end_year, 12, 31) if end_year else datetime.max
        
        # Check if paper date falls within this affiliation period
        if start_date <= paper_date <= end_date:
            return {
                'name': institution.get('name'),
                'domain': institution.get('domain'),
                'country': institution.get('country', 'UNK')
            }
            
    return None  # No matching affiliation found
```

### Configuration Components

Configuration files include:

- `venues_config.py`: Defines venues/conferences to track
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

- `name2cc.py`: Maps institution names to country codes
  ```python
  affiliation_to_country = {
      "Indian Institute of Technology Bombay": "IN",
      "IIIT Hyderabad": "IN",
      # ...
  }
  ```

- `d2cc.py`: Maps domains to country codes
  ```python
  domain_to_cc = {
      "iitb.ac.in": "IN",
      "iiit.ac.in": "IN",
      # ...
  }
  ```

- `db_config.py`: Database connection settings
  ```python
  DATABASE_URL = "sqlite:///venues.db"
  engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
  SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
  ```

### DTO (Data Transfer Objects)

The system uses DTOs to pass data between different components:

- `AuthorDTO`: Represents author information with fields for name, email, identifiers, and affiliation history
- `PaperDTO`: Represents paper details including metadata and author list

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
python -m indiaml.pipeline.patch_unk_cc5  # Optional, requires OpenRouter API key

# Generate analytics
python -m indiaml.analytics.analytics
python -m indiaml.pipeline.generate_final_jsons
python -m indiaml.pipeline.generate_summaries  # Optional, requires OpenRouter API key
```

### Adding a New Conference

To add a new conference:

1. Add a new `VenueConfig` entry to `indiaml/config/venues_config.py`:
   ```python
   VENUE_CONFIGS.append(
       VenueConfig(
           conference="NewConference",
           year=2024,
           track="Conference",
           source_adapter="openreview",
           source_id="NewConference.cc/2024/Conference",
           adapter_class="NeurIPSAdapter"  # Reuse existing adapter if compatible
       )
   )
   ```

2. If the new conference has a unique structure, create a custom adapter:
   ```python
   # indiaml/venue_adapters/new_conference_adapter.py
   from .base_adapter import BaseAdapter
   
   class NewConferenceAdapter(BaseAdapter):
       def fetch_papers(self) -> List[PaperRecord]:
           # Implementation
       
       def determine_status(self, venue_group, venueid) -> str:
           # Implementation
           
       def fetch_authors(self, author_ids) -> List[AuthorDTO]:
           # Implementation
   ```

3. Register the adapter in `adapter_factory.py`

4. Run the pipeline with the new configuration