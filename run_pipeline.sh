#!/bin/bash

# IndiaML Pipeline Runner
# Runs the complete pipeline step-by-step, stopping on any error

set -e  # Exit immediately if a command exits with a non-zero status
set -u  # Exit if an undefined variable is used

echo "Starting IndiaML Pipeline..."
echo "================================"

# Change to indiaml directory
cd indiaml

echo "Step 1: Processing venues..."
python -m indiaml.pipeline.process_venue
echo "✓ Venues processed successfully"

echo "Step 2: Processing authors..."
python -m indiaml.pipeline.process_authors
echo "✓ Authors processed successfully"

echo "Step 3: Processing paper-author mapping..."
python -m indiaml.pipeline.process_paper_author_mapping
echo "✓ Paper-author mapping processed successfully"

echo "Step 4: Patching unknown country codes (cc2)..."
python -m indiaml.pipeline.patch_unk_cc2
echo "✓ CC2 patching completed successfully"

echo "Step 5: Patching unknown country codes (cc3)..."
echo "NOTE: Inspect logs for unmatched affiliations"
python -m indiaml.pipeline.patch_unk_cc3
echo "✓ CC3 patching completed successfully"

echo "Step 6: Patching unknown country codes (cc4)..."
python -m indiaml.pipeline.patch_unk_cc4
echo "✓ CC4 patching completed successfully"

echo "Step 7: Optional LLM-based PDF workflow (cc5)..."
python -m indiaml.pipeline.patch_unk_cc5
echo "✓ CC5 patching completed successfully"

echo "Step 8: Running analytics..."
python -m indiaml.analytics.analytics
echo "✓ Analytics completed successfully"

echo "Step 9: Generating final JSONs..."
python -m indiaml.pipeline.generate_final_jsons
echo "✓ Final JSONs generated successfully"

echo "Step 10: Generating summaries..."
python -m indiaml.pipeline.generate_summaries
echo "✓ Summaries generated successfully"

echo "================================"
echo "Pipeline completed successfully!"
echo "All steps have been executed in sequence."
