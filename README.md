# Overpass QL Syntax Checker

> **🚧 Work in Progress**
>
> This project is currently under active development. While the core functionality is working, we're still:
>
> - Adding more comprehensive tests
> - Fixing edge cases in syntax validation
> - Preparing for PyPI publication
>
> Feel free to test it out, but expect some changes before the stable release!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Support](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
![Status](https://img.shields.io/badge/status-work--in--progress-orange.svg)
[![Tests](https://github.com/markmclaren/overpass-syntax-checker/actions/workflows/test.yml/badge.svg)](https://github.com/markmclaren/overpass-syntax-checker/actions/workflows/test.yml)
[![Code Quality](https://github.com/markmclaren/overpass-syntax-checker/actions/workflows/quality.yml/badge.svg)](https://github.com/markmclaren/overpass-syntax-checker/actions/workflows/quality.yml)

A comprehensive Python syntax checker for the Overpass Query Language (OverpassQL), used to query OpenStreetMap data through the Overpass API.

## Features

- **Complete lexical analysis** - Tokenizes Overpass QL source code with proper handling of:
  - String literals with escape sequences (including Unicode)
  - Numeric literals (integers, floats, scientific notation)
  - Comments (single-line `//` and multi-line `/* */`)
  - All OverpassQL operators and punctuation
  - Keywords and identifiers

- **Comprehensive syntax validation** - Validates:
  - Settings statements (`[out:json][timeout:25]`)
  - Query statements (`node`, `way`, `rel`, `nwr`, `area`)
  - Tag filters (`[amenity=restaurant]`, `[name~"regex"]`)
  - Spatial filters (bounding boxes, `around`, `poly`)
  - Block statements (`union`, `difference`, `if`, `foreach`, `for`)
  - Output statements (`out`, `out geom`, `out count`)
  - Set operations and assignments (`->.setname`)
  - Recursion operators (`<`, `<<`, `>`, `>>`)

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

- Python 3.7 or higher
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

# Run built-in test suite
overpass-ql-check --test
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
- **Spatial filters**: `(bbox)`, `(around:radius,lat,lng)`, `(poly:"coords")`
- **Identity filters**: `(id:123)`, `(id:1,2,3)`
- **Area filters**: `(area)`, `(area.setname)`, `(area:id)`
- **Member filters**: `(w)`, `(r)`, `(bn)`, `(bw)`, `(br)`
- **Date filters**: `(newer:"date")`, `(changed:"date")`
- **User filters**: `(user:"name")`, `(uid:id)`

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

## Error Handling

The syntax checker provides detailed error messages:

```
Syntax Error at line 3, column 15: Expected ';' after tag filter
Syntax Error at line 5, column 8: Invalid regex pattern: Unterminated character set
Warning at line 2, column 10: Unknown setting: custom_setting
```

## Testing

Run the built-in test suite:

```bash
overpass-ql-check --test
```

Or run the comprehensive test suite:

```bash
python -m pytest tests/
# or directly
python tests/test_package.py
```

The test suite includes:

- 20+ test cases covering various syntax scenarios
- Valid query validation
- Invalid query detection with specific error types
- Edge cases and malformed input handling
- Complex real-world query testing

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
python -m pytest tests/
# or
overpass-ql-check --test
```

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