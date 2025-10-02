#!/bin/bash
set -e 
source .venv/bin/activate
black --check --diff src/ tests/ examples/
isort --check-only --diff src/ tests/ examples/
flake8 src/ tests/ examples/ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 src/ tests/ examples/ --count --max-complexity=10 --max-line-length=88 --statistics
