# Overpass QL Syntax Checker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Support](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/markmclaren/overpass-syntax-checker/actions/workflows/test.yml/badge.svg)](https://github.com/markmclaren/overpass-syntax-checker/actions/workflows/test.yml)
[![Code Quality](https://github.com/markmclaren/overpass-syntax-checker/actions/workflows/quality.yml/badge.svg)](https://github.com/markmclaren/overpass-syntax-checker/actions/workflows/quality.yml)

A comprehensive Python syntax checker for the Overpass Query Language (OverpassQL), used to query OpenStreetMap data through the Overpass API. Now with support for advanced features including **geocoding**, **statistical aggregation**, **temporal filtering**, and **complex pipeline operations**.

## Features

- **Complete lexical analysis** - Tokenizes Overpass QL source code with proper handling of:

  - String literals with escape sequences (including Unicode)
  - Numeric literals (integers, floats, scientific notation)
  - Comments (single-line `//` and multi-line `/* */`)
  - All OverpassQL operators and punctuation
  - Keywords and identifiers
  - Template placeholders with complex syntax support

- **Comprehensive syntax validation** - Validates:

  - Settings statements (`[out:json][timeout:25]`)
  - Query statements (`node`, `way`, `rel`, `nwr`, `area`)
  - Tag filters (`[amenity=restaurant]`, `[name~"regex"]`)
  - Spatial filters (bounding boxes, `around`, `poly`)
  - Block statements (`union`, `difference`, `if`, `foreach`, `for`)
  - Output statements (`out`, `out geom`, `out count`)
  - Set operations and assignments (`->.setname`)
  - Recursion operators (`<`, `<<`, `>`, `>>`)

- **Advanced feature support** - Now includes:

  - **Geocoding syntax**: `{{geocodeArea:"location"}}` with tag filters
  - **Temporal filtering**: `[changed:"start","end"]` for historical queries
  - **Statistical aggregation**: `make` statements with backslash references
  - **Complex template expressions**: Template placeholders with assignments
  - **Pipeline operations**: Complex query chaining and data processing

- **Comprehensive test coverage** - 44 test scenarios including:

  - 20+ complex real-world queries (Berlin restaurants, public transport, etc.)
  - Historical data queries with temporal filtering
  - Statistical aggregation and data processing
  - Geocoding and area-based queries
  - Error detection and edge cases

- **Detailed error reporting** - Provides specific error messages with line and column numbers
- **Warning system** - Identifies potential issues and deprecated usage
- **Zero dependencies** - Uses only Python standard library
- **Type hints** - Full type annotation support
- **Modern packaging** - Follows Python packaging best practices

## Installation

### Local Development Installation

Since this package is not yet published to PyPI, you can install it locally:

```bash
# Clone the repository
git clone https://github.com/markmclaren/overpass-syntax-checker.git
cd overpass-syntax-checker

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Manual Installation

You can also install directly from the repository:

```bash
pip install git+https://github.com/markmclaren/overpass-syntax-checker.git
```

### Troubleshooting Installation

If the `overpass-ql-check` command is not found after installation:

1. **Check if it's in your PATH:**

   ```bash
   which overpass-ql-check
   ```

2. **Use the module directly:**

   ```bash
   python -m overpass_ql_checker.cli --test
   ```

3. **Reinstall to refresh console scripts:**

   ```bash
   pip uninstall overpass-ql-checker
   pip install overpass-ql-checker  # or your preferred installation method
   ```

4. **Check your Python environment:**
   Make sure you're installing in the same environment where you want to use it.

### Requirements

- Python 3.10 or higher
- No external dependencies (uses only Python standard library)

> **Note**: This package will be published to PyPI in the future. Once published, you'll be able to install it with `pip install overpass-ql-checker`.

## Usage

### Command Line Interface

```bash
# Check a query string directly
overpass-ql-check "node[amenity=restaurant];out;"

# Check a query from file
overpass-ql-check -f my_query.overpass

# Verbose output with tokens and detailed information
overpass-ql-check -v "node[amenity=cafe];out;"

# Check version
overpass-ql-check --version
```

### Python API

```python
from overpass_ql_checker import OverpassQLSyntaxChecker

# Create checker instance
checker = OverpassQLSyntaxChecker()

# Basic validation
query = """
[out:json][timeout:25];
area[name="Berlin"]->.searchArea;
node(area.searchArea)[amenity=restaurant];
out center;
"""

is_valid = checker.validate_query(query, verbose=True)

# Detailed analysis
result = checker.check_syntax(query)
print(f"Valid: {result['valid']}")
print(f"Errors: {result['errors']}")
print(f"Warnings: {result['warnings']}")
print(f"Tokens: {len(result['tokens'])}")
```

## API Reference

### OverpassQLSyntaxChecker

Main class for syntax checking.

#### Methods

- `check_syntax(query: str) -> Dict[str, Union[bool, List[str]]]`

  - Returns detailed validation results
  - Keys: `'valid'`, `'errors'`, `'warnings'`, `'tokens'`

- `validate_query(query: str, verbose: bool = False) -> bool`
  - Returns `True` if query is valid, `False` otherwise
  - Prints results if `verbose=True`

## Supported OverpassQL Features

### Settings

- `[out:json|xml|csv|custom|popup]` - Output format
- `[timeout:seconds]` - Query timeout
- `[maxsize:bytes]` - Memory limit
- `[bbox:south,west,north,east]` - Global bounding box
- `[date:"YYYY-MM-DDTHH:MM:SSZ"]` - Historical data
- `[diff:"date1","date2"]` - Difference queries

### Query Types

- `node` - Query for nodes
- `way` - Query for ways
- `rel`/`relation` - Query for relations
- `nwr` - Query for nodes, ways, and relations
- `nw`, `nr`, `wr` - Combined queries
- `area` - Query for areas

### Filters

- **Tag filters**: `[key]`, `[key=value]`, `[key!=value]`, `[!key]`
- **Regex filters**: `[key~"regex"]`, `[~"key-regex"~"value-regex"]`
- **Temporal filters**: `[changed:"date"]`, `[changed:"start","end"]`
- **Spatial filters**: `(bbox)`, `(around:radius,lat,lng)`, `(poly:"coords")`
- **Identity filters**: `(id:123)`, `(id:1,2,3)`
- **Area filters**: `(area)`, `(area.setname)`, `(area:id)`
- **Member filters**: `(w)`, `(r)`, `(bn)`, `(bw)`, `(br)`
- **Date filters**: `(newer:"date")`, `(changed:"date")`
- **User filters**: `(user:"name")`, `(uid:id)`

### Advanced Features

- **Template placeholders**: `{{bbox}}`, `{{geocodeArea:"location"}}`
- **Geocoding with filters**: `{{geocodeArea:"Hamburg"}}["admin_level"="4"]`
- **Statistical aggregation**: `make` statements with backslash references
- **Complex loops**: `for(t["key"])` with statistical operations
- **Pipeline operations**: Complex query chaining and data processing

### Block Statements

- **Union**: `(stmt1; stmt2;)`
- **Difference**: `(stmt1; - stmt2;)`
- **If conditions**: `if (evaluator) { ... } else { ... }`
- **Loops**: `foreach { ... }`, `for (evaluator) { ... }`
- **Complete**: `complete { ... }`
- **Retro**: `retro (date) { ... }`
- **Compare**: `compare (evaluator) { ... }`

### Output Statements

- **Modes**: `ids`, `skel`, `body`, `tags`, `meta`, `count`
- **Modifiers**: `geom`, `bb`, `center`, `asc`, `qt`, `noids`
- **Limits**: `out 100;` (numeric limit)
- **Bounding boxes**: `out geom(bbox);`

### Set Operations

- **Assignment**: `query -> .setname;`
- **Reference**: `.setname;`
- **Input specification**: `node.setname[filter];`

### Recursion

- `<` - Recurse up (find parents)
- `<<` - Recurse up relations (with transitive closure)
- `>` - Recurse down (find children)
- `>>` - Recurse down relations (with transitive closure)

## Examples

### Basic Restaurant Query

```overpassql
[out:json][timeout:25];
area[name="Berlin"]->.searchArea;
(
  node(area.searchArea)[amenity=restaurant];
  way(area.searchArea)[amenity=restaurant];
  relation(area.searchArea)[amenity=restaurant];
);
out center;
```

### Complex Query with Multiple Filters

```overpassql
[out:json][bbox:52.5,13.3,52.6,13.5];
(
  node[amenity=cafe][opening_hours~".*"](around:500,52.52,13.41);
  way[building][addr:city="Berlin"];
);
out geom;
```

### Historical Data Query

```overpassql
[out:json][date:"2020-01-01T00:00:00Z"];
node[amenity=restaurant]({{bbox}});
out;
```

### Advanced Query Examples

#### Geocoding with Area Search

```overpassql
[out:json][timeout:25];
{{geocodeArea:"Deutschland"}}->.searchArea;
node["historic"="castle"](area.searchArea);
out;
```

#### Temporal Filtering

```overpassql
[out:xml][timeout:30];
way(uid:7725447)[changed:"2019-02-11T00:00:00Z","2019-02-11T23:55:59Z"];
out meta;
```

#### Statistical Aggregation

```overpassql
[out:json][timeout:25];
{{geocodeArea:"Hamburg"}}->.searchArea;
way["highway"](area.searchArea);
for(t["highway"]) {
  make stat_highway_\1 ,val=count(ways),sum=length(sum(length()));
}
out;
```

#### Pipeline Query with Template Placeholders

```overpassql
[out:json][timeout:25];
{{geocodeArea:"Hamburg"}}["admin_level"="4"]->.bndarea;
node["amenity"="library"](area.bndarea);
relation["amenity"="library"](area.bndarea);
(area.bndarea;);>;
out;
```

## Error Handling

The syntax checker provides detailed error messages:

```
Syntax Error at line 3, column 15: Expected ';' after tag filter
Syntax Error at line 5, column 8: Invalid regex pattern: Unterminated character set
Warning at line 2, column 10: Unknown setting: custom_setting
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests with pytest
python -m pytest tests/ -v

# Run tests using the test script
./test.sh

# Or run individual test modules
python tests/test_complex_queries.py
python tests/test_overpass_checker.py
python tests/test_package.py
```

The test suite includes:

- **44 comprehensive test scenarios** covering all syntax features
- **20 complex real-world queries** including:
  - Berlin restaurants with area search and union operations
  - Public transport queries with multiple filters
  - Amenities around points with recursion
  - Historical OSM data with temporal filtering
  - Complex tag filtering with regex patterns
  - Geocoding area searches
  - Statistical aggregation with `for` loops and `make` statements
  - Pipeline queries with template placeholders
- **Valid query validation** with advanced feature support
- **Invalid query detection** with specific error types
- **Edge cases and malformed input handling**
- **Cross-platform compatibility** (Linux, macOS, Windows)

## Architecture

### OverpassQLLexer

- Converts source code into tokens
- Handles string literals, numbers, identifiers
- Supports comments and escape sequences
- Provides detailed position information

### OverpassQLParser

- Recursive descent parser for OverpassQL grammar
- Validates syntax against official specification
- Generates detailed error messages with position info
- Supports all OverpassQL language constructs

### Main Interface

- OverpassQLSyntaxChecker class provides the main API
- Combines lexer and parser functionality
- Returns structured results with errors and warnings
- Simple validation methods for easy integration

## References

- [Overpass API/Overpass QL - OpenStreetMap Wiki](https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL)
- [Overpass API Language Guide](https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide)
- [Overpass Turbo](https://overpass-turbo.eu/) - Online query builder and tester

## Test Data Attribution

Additional real-world test cases in this project include queries derived from the OverpassNL dataset:

- **OverpassNL Dataset**: [GitHub Repository](https://github.com/varunlmxd/OverpassNL) - A comprehensive collection of natural language to OverpassQL query pairs used for research and testing purposes.

These test cases help ensure the syntax checker works correctly with diverse real-world OverpassQL patterns and use cases.

## Development

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/markmclaren/overpass-syntax-checker.git
cd overpass-syntax-checker

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v
# or use the test script
./test.sh

# Run code quality checks (same as CI)
./quality.sh

# Auto-fix formatting issues
./quality-fix.sh

# Or run tools individually:
black --check src/ tests/ examples/
isort --check-only src/ tests/ examples/
flake8 src/ tests/ examples/

# Auto-fix formatting issues manually
black src/ tests/ examples/
isort src/ tests/ examples/
autopep8 --in-place --aggressive --aggressive src/ tests/ examples/ --recursive
```

### Development Tools

This project uses several code quality tools with convenient scripts:

- **`./quality.sh`**: Runs all quality checks (same as CI pipeline)
- **`./quality-fix.sh`**: Automatically fixes code formatting issues
- **`./test.sh`**: Runs the comprehensive test suite
- **`./coverage.sh`**: Runs test coverage analysis with detailed reports

**Coverage script options:**

- `./coverage.sh` - Full coverage analysis with HTML and XML reports
- `./coverage.sh --quick` - Quick terminal coverage report only
- `./coverage.sh --help` - Show coverage script usage

**Individual tools:**

- **black**: Code formatter for consistent Python style
- **isort**: Import statement organizer and formatter
- **flake8**: Linter for style guide enforcement and error detection
- **autopep8**: Automatic PEP 8 compliance fixer for additional formatting issues
- **mypy**: Static type checker for Python code
- **pytest**: Testing framework with coverage reporting

### Building for Distribution

```bash
# Build the package
python -m build

# Check the distribution
twine check dist/*

# (Future) Upload to PyPI
# twine upload dist/*
```

## License

MIT License - Feel free to use, modify, and distribute.

## Language Reference

Based on the official Overpass API documentation:

- [Overpass API/Overpass QL - OpenStreetMap Wiki](https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL)
- [OverpassQL Syntax Reference](https://osm-queries.ldodds.com/syntax-reference.html)
- [Overpass API Source Code](https://github.com/drolbr/Overpass-API)

## Limitations

- Does not validate semantic correctness (e.g., whether referenced sets exist)
- Does not perform actual query execution or data validation
- Limited validation of evaluator expressions in block statements
- No support for Overpass Turbo extensions (these are preprocessor macros)

## Contributing

This syntax checker was built by analyzing the official Overpass API documentation and source code. Contributions are welcome for:

- Additional language feature support
- Improved error messages
- Performance optimizations
- Additional test cases
- Bug fixes

## License

MIT License - Feel free to use, modify, and distribute.
