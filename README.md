# 📢 This repoistory is NOT ACTIVELY MAINTAINED. We may update it in the future, but for now, we're not putting additional resources into the project.

# 🚀 IndiaML Tracker

![Lossfunk India@ML Logo](./lossfunk-indiaml.png)

## Highlighting India's contributions to global machine learning research, one paper at a time.

[![GitHub stars](https://img.shields.io/github/stars/lossfunk/indiaml-tracker?style=social)](https://github.com/lossfunk/indiaml-tracker/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/lossfunk/indiaml-tracker?style=social)](https://github.com/lossfunk/indiaml-tracker/network/members)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)

---

## 📋 Overview

The **IndiaML Tracker** systematically identifies, analyzes, and highlights India's contributions to global machine‑learning research. Born from a Twitter exchange between *Paras Chopra* (Lossfunk Founder) and *Sohan Basak* (hard‑core technologist, building the future of human–AI interaction) in **January 2025**, the project focuses on research conducted **within Indian institutions**. By publishing transparent metrics, we aim to showcase domestic innovation and inspire the next generation of researchers.

### Why We Built This

Despite India's growing presence in top‑tier ML venues, there was **no dedicated platform** quantifying that contribution. IndiaML Tracker addresses this gap by providing institution‑level analytics grounded in openly verifiable data.

Our goals include:

- 🔍 Increasing visibility of Indian research institutions globally
- 📊 Creating benchmarks for measuring progress in ML research output
- 🤝 Identifying collaboration opportunities between institutions
- ✨ Inspiring young researchers by showcasing successful Indian contributions

---

## 🧮 Methodology of Inclusion

> **Where does our data come from?**  
> Currently, **all paper metadata is sourced from the public [OpenReview](https://openreview.net) API**. OpenReview is used by many—but not all—ML conferences. We therefore treat it as a **significant subset, not the entirety**, of relevant literature.

1. **Inclusion criterion**: A paper is counted as “Indian research” when **≥ 1 author is affiliated with an Indian organisation at the time of publication**.
2. **Optional filters**:
   - *First‑author Indian*: first listed author is India‑affiliated.
   - *Majority Indian*: > 50 % of authors are India‑affiliated.
3. **Affiliation resolution**: We use deterministic rules first (institution lookup tables), followed by **LLM‑assisted disambiguation** (via OpenRouter). Because LLMs are stochastic, errors can creep in—**please help us correct them!**
4. **Limitations**:
   - Conferences that do **not** publish to OpenReview are currently absent.
   - Pre‑prints (e.g., arXiv) are outside our present scope.
   - LLM hallucinations or missing metadata can introduce noise.

**Found a missing or mis‑classified paper?** Create an [issue](https://github.com/lossfunk/indiaml-tracker/issues) or open a pull request—we’ll review quickly.

---

## 🏛️ System Architecture

IndiaML Tracker follows a **modular, pipeline‑based architecture** that enables systematic processing of research‑paper data:

![IndiaML Architecture](./indiaml-architecture.svg)

Key design patterns:

- **Adapter Pattern** – standardises data collection from heterogeneous sources
- **Factory Pattern** – instantiates the correct adapter from config
- **Repository Pattern** – abstracts database operations
- **Pipeline Pattern** – chains discrete processing stages

> **Ongoing work**: We are actively experimenting with **additional data sources** (e.g. ACL Anthology, arXiv bulk metadata) and **more robust pipelines** (e.g. deterministic disambiguation, structured affiliation ontologies) to keep improving coverage and accuracy.

For complete technical details, see [Documentation](./DOCUMENTATION.md).

---

## 🛠️ Technologies Used

| Purpose | Stack |
|---------|-------|
| Core language | **Python 3.12+** |
| Storage | **SQLite** + **SQLAlchemy** ORM |
| Data source | **OpenReview API** |
| Affiliation resolution | **LLM integration** via OpenRouter |

---

## 🤝 How to Contribute

We welcome contributions! The **fastest** way to help is to **run the pipeline and submit data**—this expands the dataset and validates existing entries.

### 1️⃣ Run the Pipeline and Submit Data

```bash
# Clone the repository
 git clone https://github.com/lossfunk/indiaml-tracker.git
 cd indiaml-tracker

# (Recommended) set up with uv
 uv venv --python=3.12
 uv pip install .

# Alternative: standard venv
 python -m venv venv
 source venv/bin/activate   # Windows: venv\Scripts\activate
 pip install -r requirements.txt

# Add your API keys (for LLM steps)
 echo "OPENROUTER_API_KEY=your_key_here" >> .env

# Run the pipeline step‑by‑step
 python -m indiaml.pipeline.process_venue
 python -m indiaml.pipeline.process_authors
 python -m indiaml.pipeline.process_paper_author_mapping
 python -m indiaml.pipeline.patch_unk_cc2
 python -m indiaml.pipeline.patch_unk_cc3   # <-- inspect logs for unmatched affiliations
 python -m indiaml.pipeline.patch_unk_cc4
 # Optional LLM‑based PDF workflow
 python -m indiaml.pipeline.patch_unk_cc5
 # Analytics & output
 python -m indiaml.analytics.analytics
 python -m indiaml.pipeline.generate_final_jsons
 python -m indiaml.pipeline.generate_summaries
```

Then submit a **pull request** with the updated JSON files and summaries.

### 2️⃣ Verify and Correct Data

Data quality is paramount. You can help by reviewing:

- Author names / affiliations
- Institutional assignments
- Country codes

Submit corrections via PR or by opening an issue.

### 3️⃣ Other Ways to Help

- 💡 Enhance affiliation‑resolution algorithms
- ➕ Add new data sources (arXiv, ACL Anthology…)
- 📚 Improve documentation
- 🐛 Fix bugs

See [CONTRIBUTING.md](./CONTRIBUTING.md) for full guidelines.

---

## 📊 What We Deliver

- 📚 A continuously updated database of ML papers with Indian author affiliations
- 🏢 Institution‑level insights and publication trends
- 📈 Year‑over‑year tracking of India’s contribution to global ML research
- 🌐 Visualisation of collaborations between Indian and international institutions

---

## 🔧 Development Setup

### Prerequisites

- Python 3.8+
- SQLite
- Git

### Quick Start

```bash
 # 1. Clone
 git clone https://github.com/lossfunk/indiaml-tracker.git
 cd indiaml-tracker

 # 2. Virtual env & deps
 python -m venv venv
 source venv/bin/activate   # Windows: venv\Scripts\activate
 pip install -r requirements.txt

 # 3. Environment variables
 echo "OPENROUTER_API_KEY=your_api_key_here" >> .env

 # 4. Run tests
 python -m unittest discover indiaml.tests
```

---

## 🔍 Troubleshooting

If you hit issues:

1. Check the **Troubleshooting** section in [DOCUMENTATION.md](./DOCUMENTATION.md#troubleshooting).
2. Search existing [GitHub issues](https://github.com/lossfunk/indiaml-tracker/issues).
3. Open a new issue with details if it’s novel.

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=lossfunk/indiaml-tracker&type=Date)](https://www.star-history.com/#lossfunk/indiaml-tracker&Date)

---

## 📜 License

Code is released under the **MIT License** (see `LICENSE`).

> **Data notice**: Some metadata originates from third‑party conference proceedings. While we are evaluating an **open data licence** compatible with those sources, **the data itself may ultimately be published under a licence different from MIT** to comply with all relevant laws and terms. We will document any change clearly.

---

Made with ❤️ by the IndiaML Tracker team — join us in highlighting India’s contributions to global ML research!
