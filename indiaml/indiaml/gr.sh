#!/bin/bash

# Ensure a directory is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

# Recursively find and process Python files, useful for copy pasting entire codebase to LLM.
find "$1" -type f -name "*.py" | while read -r file; do
  echo "=== $file ==="
  cat "$file"
  echo
done