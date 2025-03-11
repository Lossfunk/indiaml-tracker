# 🚀 IndiaML Tracker

![Lossfunk India@ML Logo](./lossfunk-indiaml.png)

Highlighting India's contributions to global machine learning research, one paper at a time.

## 📋 Overview

The IndiaML Tracker systematically identifies, analyzes, and highlights India's contributions to global machine learning research. Born from a Twitter exchange between Paras Chopra (Lossfunk Founder) and Sohan Basak (Hardcode technologist) in January 2025, the project focuses specifically on research conducted within Indian institutions. This approach aims to showcase domestic innovation and inspire the next generation of researchers.

### Why We Built This

Despite India's growing presence in global ML research, there was no dedicated platform to quantify this contribution. The IndiaML Tracker addresses this gap by providing metrics about Indian institutions' participation in top-tier ML conferences.

Our goals include:
- Increasing visibility of Indian research institutions globally
- Creating benchmarks for measuring progress in ML research output
- Identifying collaboration opportunities between institutions
- Inspiring young researchers by showcasing successful Indian contributions

## 🤝 How to Contribute

We welcome contributions from the community! Here are the most common ways to help:

### 1️⃣ Run the Pipeline and Submit Data

This is the most valuable contribution you can make - it helps expand our dataset and verify existing information.

```bash
# Clone the repository
git clone https://github.com/lossfunk/indiaml-tracker.git
cd indiaml

# Set up environment
uv venv --python=3.11
uv pip install .

# Add your API keys in a .env file
# OPENROUTER_API_KEY=your_key_here

# Install dependencies from pyproject.toml
uv pip install .

# Run the pipeline
python -m indiaml.pipeline.process_venue
python -m indiaml.pipeline.process_authors
python -m indiaml.pipeline.process_paper_author_mapping

# Run country code resolution
python -m indiaml.pipeline.patch_unk_cc2
python -m indiaml.pipeline.patch_unk_cc3
python -m indiaml.pipeline.patch_unk_cc4

# Generate analytics
python -m indiaml.analytics.analytics
```

Then submit your updated data by creating a pull request!

### 2️⃣ Verify and Correct Data

Data quality is crucial. You can help by checking and correcting:
- Author names and affiliations
- Institutional assignments
- Country codes

For corrections, open an issue with details or submit a PR with your changes.

### 3️⃣ Other Ways to Help

<details>
<summary>Enhance existing components</summary>

You can improve:
- Affiliation resolution algorithms
- Country code resolution
- Data models

Check out the CONTRIBUTING.md file for more details.
</details>

<details>
<summary>Add new data sources</summary>

The system can be extended to include data from:
- arXiv (ML/AI categories)
- ACL Anthology
- IEEE Xplore
- ACM Digital Library

See CONTRIBUTING.md for implementation guidelines.
</details>

<details>
<summary>Improve documentation</summary>

Help us make the project more accessible through:
- Better code comments
- Updated READMEs
- Tutorials and examples
- Architecture diagrams
</details>

## 🧪 Project Structure

<details>
<summary>Click to see the full project structure</summary>

```
indiaml/
├── __init__.py
├── main.py
├── pipeline/           # Data processing pipeline components
│   ├── process_venue.py
│   ├── process_authors.py
│   ├── affiliation_checker.py
│   └── patch_unk_cc*.py
├── config/             # Configuration files
├── models/             # Data models
├── venue_adapters/     # Adapters for different data sources
├── analytics/          # Analysis and visualization
└── tests/              # Test suite
```
</details>

<details>
<summary>How the pipeline works</summary>

1. **Collect** research paper metadata from major AI conferences
2. **Analyze** author affiliations with a multi-stage approach
3. **Resolve** affiliations based on publication dates
4. **Determine** institution locations through domain knowledge and analysis
5. **Validate** data through multiple verification layers
6. **Generate** analytics and visualizations

For detailed technical documentation, see the [full documentation](./DOCUMENTATION.md).
</details>

## 📊 What We Deliver

The system provides several key outputs:

- A comprehensive database of ML research papers with Indian author affiliations
- Institutional insights and publication pattern analysis
- Year-over-year tracking of India's growing contribution to global ML research
- Visualization of research partnerships between Indian and international institutions

## 🔧 Setup for Development

<details>
<summary>Prerequisites and environment setup</summary>

### Prerequisites
- Python 3.8+
- SQLite
- Required Python packages (install via `pip install -r requirements.txt`)

### Configuration

1. Create a `.env` file in the project root:
   ```
   OPENROUTER_API_KEY=your_api_key_here  # For LLM-based affiliation resolution
   ```

2. Configure venues in `indiaml/config/venues_config.py`
</details>

## 📜 License

[MIT License](LICENSE)

---

Made with ❤️ by the IndiaML Tracker team. Join us in highlighting India's contributions to global ML research!