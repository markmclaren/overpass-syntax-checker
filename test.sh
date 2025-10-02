#!/bin/bash
set -e 
source .venv/bin/activate

# Run comprehensive test suite
echo "Running comprehensive test suite..."
python -m pytest tests/ -v

# Test CLI functionality
echo -e "\nTesting CLI functionality..."
overpass-ql-check "node[amenity=restaurant];out;" --verbose
echo "✅ CLI test passed"
