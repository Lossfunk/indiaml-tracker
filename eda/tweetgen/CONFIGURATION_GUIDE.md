# Configuration Guide for Tweet Generation Pipeline

This guide explains how to configure the tweet generation pipeline using environment variables, CLI arguments, and configuration files.

## 🔧 Configuration Methods

The pipeline supports three ways to configure settings, in order of precedence:

1. **CLI Arguments** (highest priority)
2. **Environment Variables** (medium priority)  
3. **Default Values** (lowest priority)

## 📁 Environment Variables

Create a `.env` file in the `eda/tweetgen/` directory to set default values:

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
nano .env
```

### Available Environment Variables

#### API Keys (for author profile verification)
```bash
# OpenRouter API (recommended)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=gpt-4o-mini

# Alternative: OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
```

#### Directory Paths
```bash
# Directory containing SQLite database files
DATA_DIR=data

# Directory containing analytics JSON files  
ANALYTICS_DIR=ui/indiaml-tracker/public/tracker

# Output directory for generated files
OUTPUT_DIR=eda/tweetgen/outputs
```

#### Performance Settings
```bash
# Maximum concurrent requests for author enrichment
MAX_CONCURRENT_REQUESTS=3

# Request timeout in seconds
REQUEST_TIMEOUT=30

# Delay between request batches in seconds
RATE_LIMIT_DELAY=2.0
```

#### Tweet Generation Settings
```bash
# Maximum tweet length
MAX_TWEET_LENGTH=280

# Maximum authors to mention per tweet
MAX_AUTHORS_PER_TWEET=5
```

## 🖥️ CLI Arguments

Override any setting using command line arguments:

### Basic Usage
```bash
# Use default configuration
python run_pipeline.py icml-2025

# Show current configuration
python run_pipeline.py icml-2025 --show-config
```

### Directory Configuration
```bash
# Custom data directory
python run_pipeline.py icml-2025 --data-dir /path/to/data

# Custom analytics directory
python run_pipeline.py icml-2025 --analytics-dir /path/to/analytics

# Custom output directory
python run_pipeline.py icml-2025 --output-dir /path/to/output
```

### Performance Tuning
```bash
# Increase concurrent requests for faster processing
python run_pipeline.py icml-2025 --max-concurrent 5

# Increase timeout for slow networks
python run_pipeline.py icml-2025 --request-timeout 60

# Adjust rate limiting
python run_pipeline.py icml-2025 --rate-limit-delay 1.0
```

### Tweet Generation Settings
```bash
# Longer tweets (for platforms other than Twitter)
python run_pipeline.py icml-2025 --max-tweet-length 500

# More authors per tweet
python run_pipeline.py icml-2025 --max-authors-per-tweet 10
```

### Combined Example
```bash
python run_pipeline.py icml-2025 \
  --data-dir /custom/data \
  --output-dir /custom/output \
  --max-concurrent 5 \
  --request-timeout 60 \
  --max-tweet-length 300
```

## 📄 Configuration Files

### Conference Configuration File

The pipeline can auto-detect conference files or use a configuration file:

```bash
# Save current configuration to file
python run_pipeline.py icml-2025 --save-config

# This creates: eda/tweetgen/conference_config.json
```

Example `conference_config.json`:
```json
{
  "icml-2025": {
    "sqlite_file": "venues-icml-2025-v2.db",
    "analytics_file": "icml-2025-analytics.json",
    "version": "v2"
  },
  "custom-conference": {
    "sqlite_file": "venues-custom-v1.db",
    "analytics_file": "custom-analytics.json",
    "version": "v1"
  }
}
```

### Auto-Detection

If a conference is not in the configuration file, the pipeline will try to auto-detect files:

```bash
# Will search for files matching patterns:
# data/*icml-2025*.db
# ui/indiaml-tracker/public/tracker/icml-2025*analytics*.json
python run_pipeline.py icml-2025
```

## 🎯 Common Configuration Scenarios

### Development Setup
```bash
# Fast development with minimal processing
export MAX_CONCURRENT_REQUESTS=1
export REQUEST_TIMEOUT=10
export RATE_LIMIT_DELAY=0.5

python run_pipeline.py icml-2025 --output-dir ./dev-output
```

### Production Setup
```bash
# Optimized for production
export MAX_CONCURRENT_REQUESTS=5
export REQUEST_TIMEOUT=60
export RATE_LIMIT_DELAY=2.0
export OUTPUT_DIR=/var/data/tweet-outputs

python run_pipeline.py icml-2025
```

### Custom Data Sources
```bash
# Using custom data directories
python run_pipeline.py my-conference \
  --data-dir /path/to/custom/databases \
  --analytics-dir /path/to/custom/analytics \
  --output-dir /path/to/custom/output
```

### High-Performance Processing
```bash
# Maximum performance (use with caution)
python run_pipeline.py icml-2025 \
  --max-concurrent 10 \
  --request-timeout 120 \
  --rate-limit-delay 1.0
```

## 🔍 Configuration Validation

### Check Current Configuration
```bash
# View all current settings
python run_pipeline.py icml-2025 --show-config
```

### Validate File Paths
```bash
# The pipeline will validate paths during initialization
python run_pipeline.py icml-2025 --status
```

### Test Configuration
```bash
# Run the test suite to validate configuration
python test_pipeline.py
```

## 🚨 Troubleshooting

### Common Issues

#### File Not Found Errors
```bash
# Check if files exist
python run_pipeline.py icml-2025 --show-config

# Use custom paths if needed
python run_pipeline.py icml-2025 \
  --data-dir /correct/path/to/data \
  --analytics-dir /correct/path/to/analytics
```

#### API Key Issues
```bash
# Check if API keys are detected
python run_pipeline.py icml-2025 --show-config | grep api_config

# Set API key in environment
export OPENROUTER_API_KEY=your_key_here
```

#### Permission Issues
```bash
# Ensure output directory is writable
python run_pipeline.py icml-2025 --output-dir /tmp/test-output
```

### Debug Mode
```bash
# Enable verbose logging (if implemented)
export DEBUG=1
python run_pipeline.py icml-2025
```

## 📊 Performance Guidelines

### Concurrent Requests
- **1-2**: Conservative, good for development
- **3-5**: Recommended for production
- **6-10**: High performance, may hit rate limits
- **10+**: Use with caution, may cause issues

### Request Timeout
- **10-20s**: Fast networks, development
- **30-60s**: Recommended for production
- **60-120s**: Slow networks, large conferences

### Rate Limiting
- **0.5-1.0s**: Aggressive, may hit rate limits
- **2.0s**: Recommended default
- **3.0-5.0s**: Conservative, very respectful

## 🔐 Security Considerations

### API Keys
- Never commit API keys to version control
- Use environment variables or `.env` files
- Rotate keys regularly
- Use least-privilege API keys when possible

### File Permissions
- Ensure output directories have appropriate permissions
- Be careful with custom data directories
- Validate file paths to prevent directory traversal

## 🎛️ Advanced Configuration

### Custom File Patterns
```bash
# Set custom patterns in environment
export DB_PATTERN="custom-{conference}-{version}.db"
export ANALYTICS_PATTERN="{conference}-stats.json"
```

### Multiple Environments
```bash
# Development environment
cp .env.example .env.dev
# Edit .env.dev with development settings

# Production environment  
cp .env.example .env.prod
# Edit .env.prod with production settings

# Use specific environment
ln -sf .env.dev .env  # For development
ln -sf .env.prod .env # For production
```

### Configuration Inheritance
```bash
# Base configuration in .env
# Override specific settings via CLI
python run_pipeline.py icml-2025 --max-concurrent 10
```

## 📝 Configuration Best Practices

1. **Use Environment Variables** for sensitive data (API keys)
2. **Use CLI Arguments** for one-off overrides
3. **Use Configuration Files** for complex conference mappings
4. **Document Custom Configurations** in your project
5. **Test Configurations** before production use
6. **Monitor Performance** and adjust settings as needed
7. **Keep Backups** of working configurations

## 🔄 Migration from Hardcoded Configuration

If you were using the pipeline before this configuration system:

1. **Backup existing outputs** (they won't be affected)
2. **Create `.env` file** with your preferred settings
3. **Test with `--show-config`** to verify settings
4. **Update any scripts** to use new CLI arguments
5. **Remove any hardcoded paths** from custom code

The pipeline maintains backward compatibility - existing functionality will work with default settings.

---

For more examples and advanced usage, see the main [PIPELINE_README.md](PIPELINE_README.md).
