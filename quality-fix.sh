#!/bin/bash
set -e 
source .venv/bin/activate

echo "🔧 Fixing code formatting..."
echo "================================="

echo "📝 Running black (code formatter)..."
black src/ tests/ examples/

echo "📦 Running isort (import organizer)..."
isort src/ tests/ examples/

echo "🧹 Running autopep8 (PEP 8 compliance fixer)..."
autopep8 --in-place --aggressive --aggressive src/ tests/ examples/ --recursive

echo "✅ Code formatting fixes applied!"
echo ""
echo "💡 Run ./quality.sh to check if there are any remaining issues."