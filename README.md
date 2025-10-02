# Overpass QL Syntax Checker

[![PyPI version](https://badge.fury.io/py/overpass-ql-checker.svg)](https://badge.fury.io/py/overpass-ql-checker)
[![Python Support](https://img.shields.io/pypi/pyversions/overpass-ql-checker.svg)](https://pypi.org/project/overpass-ql-checker/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

```bash
pip install overpass-ql-checker
```

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
python overpass_ql_syntax_checker.py --test
```

The test suite includes:
- 20+ test cases covering various syntax scenarios
- Valid query validation
- Invalid query detection with specific error types
- Edge cases and malformed input handling

## Architecture

### OverpassQLLexer
- Converts source code into tokens
- Handles all OverpassQL literals, operators, and keywords
- Provides detailed position tracking for error reporting
- Supports Unicode escape sequences and proper string handling

### OverpassQLParser  
- Recursive descent parser for OverpassQL grammar
- Validates syntax structure and semantics
- Generates detailed error and warning messages
- Supports all OverpassQL language constructs

### OverpassQLSyntaxChecker
- Main interface class
- Combines lexer and parser functionality
- Provides both programmatic API and CLI interface

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