# 🚀 IndiaML Tracker

![Lossfunk India@ML Logo](./lossfunk-indiaml.png)

Highlighting India's contributions to global machine learning research, one paper at a time.

## 📋 Overview

The IndiaML Tracker systematically identifies, analyzes, and highlights India's contributions to global machine learning research. Born from a Twitter exchange between Paras Chopra (Lossfunk Founder) and Sohan Basak (Hardcore technologist, trying to build the future of human AI interaction) in January 2025, the project focuses specifically on research conducted within Indian institutions. This approach aims to showcase domestic innovation and inspire the next generation of researchers.

### Why We Built This

Despite India's growing presence in global ML research, there was no dedicated platform to quantify this contribution. The IndiaML Tracker addresses this gap by providing metrics about Indian institutions' participation in top-tier ML conferences.

Our goals include:
- Increasing visibility of Indian research institutions globally
- Creating benchmarks for measuring progress in ML research output
- Identifying collaboration opportunities between institutions
- Inspiring young researchers by showcasing successful Indian contributions

## 🏛️ System Architecture

IndiaML Tracker follows a modular, pipeline-based architecture that enables systematic processing of research paper data:

![IndiaML Architecture](./indiaml-architecture.svg)

The system employs several design patterns (Adapter, Factory, Repository) to ensure maintainability and extensibility. For complete technical details, please refer to our [Documentation](./DOCUMENTATION.md).

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

# Run the pipeline
python -m indiaml.pipeline.process_venue
python -m indiaml.pipeline.process_authors
python -m indiaml.pipeline.process_paper_author_mapping
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

- **Enhance existing components**: Improve algorithms for affiliation resolution or data processing
- **Add new data sources**: Extend the system to include data from arXiv, ACL Anthology, etc.
- **Improve documentation**: Make the project more accessible through better documentation

For detailed contribution guidelines, see [CONTRIBUTING.md](./CONTRIBUTING.md).

## 📊 What We Deliver

The system provides several key outputs:

- A comprehensive database of ML research papers with Indian author affiliations
- Institutional insights and publication pattern analysis
- Year-over-year tracking of India's growing contribution to global ML research
- Visualization of research partnerships between Indian and international institutions

## 🔧 Development Setup

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

For detailed technical documentation, see [DOCUMENTATION.md](./DOCUMENTATION.md).

## 📜 License

[MIT License](LICENSE)

---

Made with ❤️ by the IndiaML Tracker team. Join us in highlighting India's contributions to global ML research!