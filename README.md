# 🚀 IndiaML Tracker

![Lossfunk India@ML Logo](./lossfunk-indiaml.png)

## Highlighting India's contributions to global machine learning research, one paper at a time.

[![GitHub stars](https://img.shields.io/github/stars/lossfunk/indiaml-tracker?style=social)](https://github.com/lossfunk/indiaml-tracker/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/lossfunk/indiaml-tracker?style=social)](https://github.com/lossfunk/indiaml-tracker/network/members)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)

## 📋 Overview

The IndiaML Tracker systematically identifies, analyzes, and highlights India's contributions to global machine learning research. Born from a Twitter exchange between Paras Chopra (Lossfunk Founder) and Sohan Basak (Hardcore technologist, trying to build the future of human AI interaction) in January 2025, the project focuses specifically on research conducted within Indian institutions. This approach aims to showcase domestic innovation and inspire the next generation of researchers.

### Why We Built This

Despite India's growing presence in global ML research, there was no dedicated platform to quantify this contribution. The IndiaML Tracker addresses this gap by providing metrics about Indian institutions' participation in top-tier ML conferences.

Our goals include:
- 🔍 Increasing visibility of Indian research institutions globally
- 📊 Creating benchmarks for measuring progress in ML research output
- 🤝 Identifying collaboration opportunities between institutions
- ✨ Inspiring young researchers by showcasing successful Indian contributions

## 🏛️ System Architecture

IndiaML Tracker follows a modular, pipeline-based architecture that enables systematic processing of research paper data:

![IndiaML Architecture](./indiaml-architecture.svg)

The system employs several design patterns to ensure maintainability and extensibility:

- **Adapter Pattern**: Standardizes data collection from various sources
- **Factory Pattern**: Creates appropriate adapters based on configuration
- **Repository Pattern**: Abstracts database operations
- **Pipeline Pattern**: Structures data processing into discrete stages

For complete technical details, please refer to our [Documentation](./DOCUMENTATION.md).

## 🛠️ Technologies Used

- **Python 3.8+**: Core development language
- **SQLite**: Lightweight database for data storage
- **SQLAlchemy**: ORM for database operations
- **OpenReview API**: Primary data source for paper metadata
- **LLM Integration**: Advanced affiliation resolution (via OpenRouter)

## 🤝 How to Contribute

We welcome contributions from the community! Here are the most common ways to help:

### 1️⃣ Run the Pipeline and Submit Data

This is the most valuable contribution you can make - it helps expand our dataset and verify existing information.

```bash
# Clone the repository
git clone https://github.com/lossfunk/indiaml-tracker.git
cd indiaml

# Set up environment with uv (recommended)
uv venv --python=3.12
uv pip install .

# Alternative setup with pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Add your API keys in a .env file
# OPENROUTER_API_KEY=your_key_here

# Run the pipeline
python -m indiaml.pipeline.process_venue
python -m indiaml.pipeline.process_authors
python -m indiaml.pipeline.process_paper_author_mapping
python -m indiaml.pipeline.patch_unk_cc2
python -m indiaml.pipeline.patch_unk_cc3
```

After running cc3, please check the logs for unmatched affiliations. At this point, you may want to find ways to add them to `name2cc.py` file, either manually or using a service like ChatGPT. We leave this as a manual step as it requires careful judgment and LLMs are prone to hallucinations.

```bash
# Complete remaining pipeline steps
python -m indiaml.pipeline.patch_unk_cc4

# Optional: LLM-based PDF parsed workflow (requires API key)
python -m indiaml.pipeline.patch_unk_cc5

# Generate analytics and output
python -m indiaml.analytics.analytics
python -m indiaml.pipeline.generate_final_jsons
python -m indiaml.pipeline.generate_summaries
```

Then submit your updated data by creating a pull request! (don't forget to verify the index.json as well as the generated summaries)

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
- **Fix bugs**: Address open issues in the GitHub repository

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
- Git

### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/lossfunk/indiaml-tracker.git
   cd indiaml-tracker
   ```

2. Set up environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:
   ```
   OPENROUTER_API_KEY=your_api_key_here  # For LLM-based affiliation resolution
   ```

4. Run tests to verify your setup:
   ```bash
   python -m unittest discover indiaml.tests
   ```

For detailed technical documentation, see [DOCUMENTATION.md](./DOCUMENTATION.md).

## 🔍 Troubleshooting

If you encounter issues during setup or while running the pipeline:

1. Check the [Troubleshooting section](./DOCUMENTATION.md#troubleshooting) in our documentation
2. Look for similar issues in our [GitHub Issues](https://github.com/lossfunk/indiaml-tracker/issues)
3. If your issue is new, please open a detailed bug report

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=lossfunk/indiaml-tracker&type=Date)](https://www.star-history.com/#lossfunk/indiaml-tracker&Date)


## FAQ

### What is "Indian Research"
- How we define that is "at least one author must be affiliated with an indian organization at the time of publication of the paper"
- There are two filters "First author Indian" and "Majory Authors Indian", this will update appropriate filters.

## 📜 License

[MIT License](LICENSE)

---

Made with ❤️ by the IndiaML Tracker team. Join us in highlighting India's contributions to global ML research!
