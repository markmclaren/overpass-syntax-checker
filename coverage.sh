#!/bin/bash
set -e 
source .venv/bin/activate

# Function to show help
show_help() {
    echo "📊 Coverage Analysis Script"
    echo "=========================="
    echo ""
    echo "Usage: ./coverage.sh [options]"
    echo ""
    echo "Options:"
    echo "  --quick, -q    Run tests with basic terminal coverage report only"
    echo "  --help, -h     Show this help message"
    echo ""
    echo "Default behavior (no options):"
    echo "  • Runs full test suite with coverage"
    echo "  • Generates terminal, HTML, and XML coverage reports"
    echo "  • Opens HTML report in browser automatically"
    echo ""
    echo "Examples:"
    echo "  ./coverage.sh              # Full coverage analysis"
    echo "  ./coverage.sh --quick      # Quick terminal report only"
    echo "  ./coverage.sh -q           # Same as --quick"
    echo "  ./coverage.sh --help       # Show this help"
}

# Parse command line arguments
QUICK_MODE=false
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
elif [[ "$1" == "--quick" || "$1" == "-q" ]]; then
    QUICK_MODE=true
fi

echo "📊 Running test coverage analysis..."
echo "===================================="

if [ "$QUICK_MODE" = true ]; then
    echo "⚡ Quick mode: Running tests with basic coverage report..."
    python -m pytest tests/ --cov=src --cov-report=term
    echo ""
    echo "💡 Run './coverage.sh' (without --quick) for detailed HTML and XML reports."
else
    # Run tests with comprehensive coverage
    echo "🧪 Executing test suite with coverage tracking..."
    python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml

    echo ""
    echo "📈 Coverage reports generated:"
    echo "  • Terminal report: displayed above"
    echo "  • HTML report: htmlcov/index.html"
    echo "  • XML report: coverage.xml"

    echo ""
    echo "🌐 To view the detailed HTML coverage report:"
    echo "  open htmlcov/index.html"

    # Check if we can open the HTML report automatically
    if command -v open &> /dev/null; then
        echo ""
        echo "🚀 Opening HTML coverage report in browser..."
        open htmlcov/index.html
    elif command -v xdg-open &> /dev/null; then
        echo ""
        echo "🚀 Opening HTML coverage report in browser..."
        xdg-open htmlcov/index.html
    fi
fi

echo ""
echo "✅ Coverage analysis complete!"