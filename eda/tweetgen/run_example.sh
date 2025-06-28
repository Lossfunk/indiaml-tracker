#!/bin/bash

# Tweet Generator Example Script
# This script demonstrates how to use the tweet generator

echo "🎯 Tweet Generator for Research Papers"
echo "======================================"
echo ""

# Check if Exa API key is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide your Exa API key as the first argument"
    echo ""
    echo "Usage: ./run_example.sh YOUR_EXA_API_KEY"
    echo ""
    echo "Get your API key from: https://exa.ai"
    exit 1
fi

EXA_API_KEY="$1"

echo "🔧 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "🧪 Creating test dataset..."
python3 test_script.py

echo ""
echo "🚀 Running tweet generator on test data..."
python3 tweet_generator.py test_papers.json --exa-api-key "$EXA_API_KEY" --output-dir test_output/ --output-file test_tweets.md

echo ""
echo "📊 Results:"
echo "- Generated cards: test_output/"
echo "- Tweet threads: test_tweets.md"
echo ""

if [ -f "test_tweets.md" ]; then
    echo "✅ Success! Tweet generation completed."
    echo ""
    echo "📄 Sample output:"
    head -30 test_tweets.md
else
    echo "❌ Something went wrong. Check the error messages above."
fi

echo ""
echo "🎉 To run on the full ICML 2025 dataset:"
echo "python3 tweet_generator.py ../../ui/indiaml-tracker/public/tracker/icml-2025.json --exa-api-key $EXA_API_KEY"
