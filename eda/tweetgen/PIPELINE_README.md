# Tweet Generation Pipeline

A comprehensive, production-ready pipeline for generating tweet threads from conference data with robust checkpointing, author enrichment, and analytics integration.

## 🚀 Features

### Core Pipeline
- **SQLite Data Extraction**: Reads papers and authors from conference databases
- **Author Profile Enrichment**: Automatically discovers Twitter, Google Scholar, LinkedIn profiles
- **Analytics Integration**: Processes conference analytics for contextual insights
- **Tweet Thread Generation**: Creates structured tweet threads with proper formatting
- **Markdown Export**: Generates comprehensive markdown documentation
- **Robust Checkpointing**: Resume from any step if interrupted
- **Progress Tracking**: Real-time progress monitoring and status reporting

### Advanced Capabilities
- **Concurrent Processing**: Efficient batch processing with rate limiting
- **LLM Integration**: Smart profile verification using OpenAI/OpenRouter
- **Quality Detection**: Identifies spotlight papers and oral presentations
- **Domain Hashtags**: Automatically generates relevant hashtags from paper titles
- **Social Media Integration**: Proper Twitter mentions and handle formatting
- **Error Recovery**: Graceful handling of network failures and timeouts

## 📋 Prerequisites

### Required Files
- SQLite database with conference data (in `data/` directory)
- Analytics JSON file (in `ui/indiaml-tracker/public/tracker/` directory)
- Environment configuration (`.env` file)

### Dependencies
```bash
pip install -r pipeline_requirements.txt
playwright install chromium
```

## ⚙️ Setup

### 1. Environment Configuration
Create a `.env` file in the `eda/tweetgen/` directory:

```bash
# OpenRouter API (recommended)
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=gpt-4o-mini

# Alternative: OpenAI API
OPENAI_API_KEY=your_openai_key_here
```

### 2. Verify Data Files
Ensure you have the required data files:
- `data/venues-icml-2025-v2.db` (or appropriate conference database)
- `ui/indiaml-tracker/public/tracker/icml-2025-analytics.json` (or appropriate analytics file)

## 🎯 Usage

### Quick Start
```bash
cd eda/tweetgen
python run_pipeline.py icml-2025
```

### Available Commands

#### Run Pipeline
```bash
# Basic usage
python run_pipeline.py icml-2025

# Force restart from beginning
python run_pipeline.py icml-2025 --force-restart

# Resume from specific step
python run_pipeline.py icml-2025 --resume-from author_enrichment

# Custom output directory
python run_pipeline.py icml-2025 --output-dir /path/to/output
```

#### Check Status
```bash
python run_pipeline.py icml-2025 --status
```

#### List Available Steps
```bash
python run_pipeline.py icml-2025 --list-steps
```

### Supported Conferences
- `icml-2025`
- `icml-2024`
- `iclr-2025`
- `iclr-2024`
- `neurips-2024`

## 🔄 Pipeline Steps

The pipeline consists of 8 sequential steps:

1. **Initialize**: Validate inputs and setup
2. **Data Extraction**: Get conference metadata
3. **SQLite Processing**: Extract papers and authors
4. **Author Enrichment**: Find social media profiles
5. **Analytics Processing**: Process conference analytics
6. **Tweet Generation**: Create tweet thread JSON
7. **Markdown Generation**: Generate documentation
8. **Finalize**: Organize outputs and cleanup

## 📊 Output Structure

```
eda/tweetgen/outputs/{conference}/
├── checkpoints/                    # Checkpoint files for resuming
│   ├── processing_state.json      # Pipeline state
│   ├── raw_papers.json            # Extracted papers
│   ├── raw_authors.json           # Extracted authors
│   ├── enriched_authors.json      # Authors with social profiles
│   ├── processed_analytics.json   # Processed analytics
│   └── tweet_thread.json          # Generated tweet thread
├── tweet_thread.json              # Final tweet thread
├── tweet_thread.md                # Markdown documentation
├── summary.md                     # Executive summary
└── pipeline_summary.json          # Pipeline metadata
```

## 📝 Output Formats

### Tweet Thread JSON
```json
{
  "conference": "ICML",
  "year": 2025,
  "generated_at": "2025-06-29T14:30:00",
  "metadata": {
    "total_tweets": 15,
    "total_papers": 12,
    "processing_time": "45m"
  },
  "analytics_summary": {
    "india_papers": 12,
    "global_rank": 8,
    "acceptance_rate": "2.1%"
  },
  "tweets": [
    {
      "id": 1,
      "type": "analytics_opener",
      "content": "🇮🇳 India @ ICML 2025 Thread 🧵\n\n...",
      "mentions": [],
      "hashtags": ["#ICML2025", "#IndiaML"],
      "metadata": {...}
    }
  ]
}
```

### Individual Tweet Structure
```json
{
  "id": 3,
  "type": "paper",
  "paper_id": "12345",
  "content": "📄 Deep Learning for Climate Modeling\n\n🌟 Spotlight 👥 Authors: @researcher1, Jane Doe\n🏛️ IIT Delhi\n🎯 Spotlight Paper\n\n#ICML2025 #DeepLearning",
  "mentions": ["@researcher1"],
  "hashtags": ["#ICML2025", "#DeepLearning"],
  "authors": [
    {
      "name": "John Smith",
      "affiliation": "IIT Delhi",
      "twitter_handle": "@researcher1",
      "google_scholar": "https://scholar.google.com/...",
      "position": 0
    }
  ],
  "metadata": {
    "character_count": 145,
    "is_spotlight": true,
    "is_oral": false,
    "author_count": 2
  }
}
```

## 🔧 Configuration

### Pipeline Configuration
The pipeline automatically maps conferences to their data files:

```python
config_map = {
    "icml-2025": {
        "sqlite_file": "venues-icml-2025-v2.db",
        "analytics_file": "icml-2025-analytics.json"
    }
}
```

### Author Enrichment Settings
- **Concurrent requests**: 3 (configurable)
- **Request timeout**: 30 seconds
- **Rate limiting**: 2 seconds between batches
- **Browser**: Chromium (headless)

### Tweet Generation Settings
- **Max tweet length**: 280 characters
- **Max authors per tweet**: 5
- **Quality paper priority**: Spotlights > Orals > Regular

## 🛠️ Advanced Usage

### Resume from Specific Step
If the pipeline fails or is interrupted:

```bash
# Check current status
python run_pipeline.py icml-2025 --status

# Resume from where it left off
python run_pipeline.py icml-2025

# Or resume from specific step
python run_pipeline.py icml-2025 --resume-from analytics_processing
```

### Custom Processing
For advanced users, you can import and use pipeline components directly:

```python
from pipeline.main_pipeline import TweetGenerationPipeline

pipeline = TweetGenerationPipeline("icml-2025")
results = await pipeline.run()
```

## 🚨 Error Handling

The pipeline includes comprehensive error handling:

- **Network failures**: Automatic retries with exponential backoff
- **Missing data**: Graceful degradation with warnings
- **API failures**: Fallback to basic processing
- **Interrupted processing**: Automatic checkpoint saving
- **Invalid inputs**: Clear error messages with suggestions

### Common Issues

#### Missing API Keys
```
⚠️ Warning: No OpenAI/OpenRouter API key found. Profile verification will be basic.
```
**Solution**: Add API keys to `.env` file

#### Missing Data Files
```
❌ Error: SQLite file not found: data/venues-icml-2025-v2.db
```
**Solution**: Ensure data files are in correct locations

#### Network Timeouts
```
❌ Error processing Author Name: TimeoutError
```
**Solution**: Pipeline continues with basic data; re-run to retry failed authors

## 📈 Performance

### Typical Processing Times
- **Small conference** (50 papers): 10-15 minutes
- **Medium conference** (200 papers): 30-45 minutes  
- **Large conference** (500+ papers): 1-2 hours

### Optimization Tips
- Use SSD storage for faster checkpoint I/O
- Ensure stable internet connection for author enrichment
- Run during off-peak hours for better web scraping success rates

## 🔍 Monitoring

### Real-time Progress
The pipeline provides detailed progress information:

```
🚀 Starting Tweet Generation Pipeline for icml-2025
============================================================

🔧 Step 1: Initialize
  ✅ SQLite file: data/venues-icml-2025-v2.db
  ✅ Analytics file: ui/indiaml-tracker/public/tracker/icml-2025-analytics.json
  ✅ Initialization complete

🗄️ Step 3: SQLite Processing
  📄 Found 156 papers with Indian authors
  👥 Found 312 unique authors
  📊 Statistics: 156 papers, 89 Indian authors
  ✅ SQLite processing complete

🔍 Step 4: Author Enrichment
  🔍 Processing: Dr. Rajesh Kumar
    🐦 Found Twitter: https://x.com/rajesh_ml
    🎓 Found Scholar: https://scholar.google.com/citations?user=...
  ✅ Author enrichment complete
```

### Status Monitoring
```bash
python run_pipeline.py icml-2025 --status
```

Output:
```
📊 Pipeline Status:
========================================
Conference: icml-2025
Status: running
Progress: 62.5%
Current step: author_enrichment

✅ Completed steps (5):
  • initialize
  • data_extraction
  • sqlite_processing
  • author_enrichment
  • analytics_processing

📈 Progress:
  • total_papers: 156
  • processed_authors: 195
  • enriched_authors: 195
```

## 🤝 Contributing

### Adding New Conferences
1. Add database and analytics files to appropriate directories
2. Update `config_map` in `main_pipeline.py`
3. Test with a small subset of data

### Extending Functionality
- **New social platforms**: Extend `AuthorEnricher` class
- **Custom tweet formats**: Modify `TweetGenerator` class
- **Additional analytics**: Enhance `AnalyticsProcessor` class

## 📄 License

This pipeline is part of the India@ML project and follows the same licensing terms.

## 🆘 Support

For issues and questions:
1. Check the error messages and logs
2. Verify all prerequisites are met
3. Try resuming from the last successful step
4. Check network connectivity for author enrichment
5. Ensure API keys are properly configured

## 🔄 Version History

- **v1.0.0**: Initial release with full pipeline functionality
- **v1.1.0**: Added resume capabilities and improved error handling
- **v1.2.0**: Enhanced author enrichment with LLM verification
- **v1.3.0**: Added markdown generation and comprehensive documentation
