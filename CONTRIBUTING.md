# Contributing to IndiaML Tracker

Thank you for your interest in contributing to the IndiaML Tracker project! Your contributions help us build a more comprehensive picture of India's contributions to the global machine learning landscape.

This document outlines various ways you can contribute to the project, along with guidelines to ensure smooth collaboration.

## Table of Contents

- [Why Contribute?](#why-contribute)
- [Code of Conduct](#code-of-conduct)
- [Types of Contributions](#types-of-contributions)
  - [Running the Pipeline and Submitting Data](#running-the-pipeline-and-submitting-data)
  - [Verifying and Correcting Data](#verifying-and-correcting-data)
  - [Enhancing Existing Components](#enhancing-existing-components)
  - [Adding New Data Sources](#adding-new-data-sources)
  - [Improving Documentation](#improving-documentation)
  - [Addressing Issues](#addressing-issues)
- [Development Setup](#development-setup)
- [Contribution Process](#contribution-process)
  - [Pull Request Guidelines](#pull-request-guidelines)
  - [Code Style and Standards](#code-style-and-standards)
  - [Formatting Guidelines](#formatting-guidelines)
- [Community Guidelines](#community-guidelines)

## Why Contribute?

The IndiaML Tracker aims to spotlight India's contributions to machine learning research. By contributing, you help:

1. Increase visibility of Indian researchers and institutions in the global ML community
2. Create a more accurate and comprehensive dataset of ML research affiliations
3. Provide valuable insights into research trends and collaboration patterns
4. Inspire the next generation of Indian ML researchers

Your contributions, large or small, directly support these goals.

## Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. By participating in this project, you agree to abide by our Code of Conduct.

### Our Pledge

In the interest of fostering an open and welcoming environment, we pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

Examples of unacceptable behavior include:

- The use of sexualized language or imagery and unwelcome sexual attention or advances
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information, such as a physical or electronic address, without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team at [maintainer email]. All complaints will be reviewed and investigated and will result in a response that is deemed necessary and appropriate to the circumstances. The project team is obligated to maintain confidentiality with regard to the reporter of an incident.

Project maintainers who do not follow or enforce the Code of Conduct in good faith may face temporary or permanent repercussions as determined by other members of the project's leadership.

## Types of Contributions

### Running the Pipeline and Submitting Data

One of the most valuable contributions is running the data pipeline and submitting the results. This helps expand our dataset and verify existing data.

**Steps to contribute data:**

1. **Set up your environment:**
   ```bash
   git clone https://github.com/lossfunk/indiaml-tracker.git
   cd indiaml
   uv venv --python=3.11
   uv pip install .
   ```

2. **Create a .env file with necessary API keys:**
   ```
   OPENROUTER_API_KEY=your_api_key_here  # For LLM-based affiliation resolution
   ```

3. **Run the pipeline:**
   ```bash
   # Fetch and process data for configured venues
   python -m indiaml.pipeline.process_venue
   python -m indiaml.pipeline.process_authors
   python -m indiaml.pipeline.process_paper_author_mapping
   
   # Run country code resolution scripts
   python -m indiaml.pipeline.patch_unk_cc2
   python -m indiaml.pipeline.patch_unk_cc3
   python -m indiaml.pipeline.patch_unk_cc4
   
   # Optional advanced resolution (requires API key)
   python -m indiaml.pipeline.patch_unk_cc5
   
   # Generate analytics output
   python -m indiaml.analytics.analytics
   ```

4. **Submit your data:**
   - Create a new branch: `git checkout -b data-contribution-YYYYMMDD`
   - Add your updated database or analytics output
   - Commit and push your changes
   - Open a pull request with a clear description of the data you've added

**Note:** If you focus on specific conferences or years not already in our database, please mention this in your PR description.

### Verifying and Correcting Data

Data quality is crucial. You can help by verifying and correcting existing data.

**Steps to verify data:**

1. **Identify papers to review:**
   - Focus on papers from your institution or field of expertise
   - Or pick papers with "UNK" country codes or missing affiliations

2. **Check for accuracy:**
   - Verify author names and affiliations
   - Confirm correct institutional assignments
   - Check country codes

3. **Submit corrections:**
   - For minor corrections, open an issue with details
   - For multiple corrections, create a JSON file with corrections and submit a PR
   - Format: `{"paper_id": "...", "corrections": [{"author_id": "...", "correct_affiliation": "...", "correct_country": "..."}]}`

### Enhancing Existing Components

You can improve existing components of the system:

1. **Affiliation Checker (`indiaml/pipeline/affiliation_checker.py`):**
   - Improve the algorithm for resolving affiliations
   - Add handling for edge cases

2. **Country Code Resolution (`indiaml/pipeline/patch_unk_cc*.py`):**
   - Enhance algorithms for determining country codes
   - Add additional mapping entries to `indiaml/config/name2cc.py` and `indiaml/config/d2cc.py`

3. **Data Models (`indiaml/models/`):**
   - Extend models to capture additional metadata
   - Optimize database schema for performance

### Adding New Data Sources

Expanding the system to include data from additional sources is extremely valuable:

1. **Create a new adapter:**
   ```python
   # indiaml/venue_adapters/new_source_adapter.py
   from .base_adapter import BaseAdapter
   
   class NewSourceAdapter(BaseAdapter):
       def fetch_papers(self) -> List[PaperDTO]:
           # Implementation for fetching papers
           
       def determine_status(self, venue_group, venueid) -> str:
           # Implementation for determining paper status
           
       def fetch_authors(self, author_ids) -> List[AuthorDTO]:
           # Implementation for fetching author details
   ```

2. **Register the adapter in the factory:**
   ```python
   # indiaml/venue_adapters/adapter_factory.py
   adapter_classes = {
       # Existing adapters...
       "NewSourceAdapter": NewSourceAdapter,
   }
   ```

3. **Add configuration:**
   ```python
   # indiaml/config/venues_config.py
   VENUE_CONFIGS.append(
       VenueConfig(
           conference="NewConference",
           year=2024,
           track="MainTrack",
           source_adapter="new_source",
           source_id="NewConference/2024/MainTrack",
           adapter_class="NewSourceAdapter"
       )
   )
   ```

**Potential new data sources to consider:**
- arXiv (ML/AI categories)
- ACL Anthology
- IEEE Xplore
- ACM Digital Library
- AAAI Digital Library
- Journal databases (Elsevier, Springer, etc.)

### Improving Documentation

Clear documentation is essential for project adoption:

- Add or improve code comments
- Update README.md with new features or clearer instructions
- Create or enhance tutorials and examples
- Add diagrams explaining system architecture or workflows

### Addressing Issues

You can help by addressing open issues in the GitHub repository:

1. Find an issue labeled "good first issue" or "help wanted"
2. Comment on the issue to let others know you're working on it
3. Submit a PR with your solution

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/indiaml-tracker.git
   cd indiaml-tracker
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file with required API keys.

5. **Run tests to ensure everything is working:**
   ```bash
   python -m unittest discover indiaml.tests
   ```

## Contribution Process

### Pull Request Guidelines

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, well-documented code
   - Add tests for new functionality
   - Ensure all tests pass

3. **Commit your changes:**
   - Use clear, descriptive commit messages
   - Reference issue numbers if applicable

4. **Submit a pull request:**
   - Provide a clear description of the changes
   - Explain how to test the changes
   - Link to relevant issues

5. **Respond to review feedback:**
   - Be open to suggestions
   - Make requested changes promptly

### Code Style and Standards

- Follow PEP 8 guidelines for Python code
- Use type hints where appropriate
- Write docstrings for functions and classes
- Include unit tests for new functionality
- Aim for 80% test coverage for new code

### Formatting Guidelines

Consistent formatting makes the codebase more maintainable and easier to understand. Please adhere to the following guidelines:

#### Python Code Formatting

- Use 4 spaces for indentation (no tabs)
- Maximum line length of 88 characters (compatible with Black formatter)
- Use Black and isort for automated formatting:
  ```bash
  pip install black isort
  black indiaml/
  isort indiaml/
  ```
- Follow Google-style docstrings for functions and classes:
  ```python
  def function_name(param1: type, param2: type) -> return_type:
      """Short description of the function.
      
      More detailed description if needed.
      
      Args:
          param1: Description of param1
          param2: Description of param2
          
      Returns:
          Description of return value
          
      Raises:
          ExceptionType: When and why this exception is raised
      """
  ```

#### Commit Messages

- Use the imperative mood ("Add feature" not "Added feature")
- First line should be 50 characters or less
- Start with a capital letter
- Do not end with a period
- Reference issue numbers at the end of the line when applicable
- Include a more detailed description after the first line if necessary, separated by a blank line

Example:
```
Add ICML 2023 adapter and configuration

- Implement ICMLAdapter for 2023 conference structure
- Add venue configuration in venues_config.py
- Update adapter factory to support the new adapter

Fixes #42
```

#### Documentation Formatting

- Use Markdown for all documentation files
- Headers should use the ATX-style (# for h1, ## for h2, etc.)
- Use code blocks with language specification for code samples
- Include links to relevant sections/files when referencing other parts of the project
- Keep line length reasonable (around 80-100 characters) for better readability in plain text

#### SQL and Database Schema Changes

- Include both the SQL statements and ORM model changes when modifying the database schema
- Add a database migration script if necessary
- Document changes to the database schema in comments

## Community Guidelines

- Be respectful and inclusive in all interactions
- Provide constructive feedback
- Acknowledge the work of others
- Ask for help when needed
- Help others learn and grow

Thank you for contributing to the IndiaML Tracker project! Your efforts help highlight India's contributions to the global machine learning landscape.