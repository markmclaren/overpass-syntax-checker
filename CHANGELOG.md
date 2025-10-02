# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-02

### Added
- Initial release of overpass-ql-checker
- Complete lexical analysis for Overpass QL
- Comprehensive syntax validation
- Support for all major Overpass QL constructs:
  - Settings statements (`[out:json][timeout:25]`)
  - Query statements (`node`, `way`, `rel`, `nwr`, `area`)
  - Tag filters (`[amenity=restaurant]`, `[name~"regex"]`)
  - Spatial filters (bounding boxes, `around`, `poly`)
  - Block statements (`union`, `difference`, `if`, `foreach`, `for`)
  - Output statements (`out`, `out geom`, `out count`)
  - Set operations and assignments (`->.setname`)
  - Recursion operators (`<`, `<<`, `>`, `>>`)
- Detailed error reporting with line and column numbers
- Warning system for potential issues
- Command-line interface (`overpass-ql-check`)
- Python API for programmatic usage
- Comprehensive test suite
- Type hints and modern Python packaging

### Features
- **Zero dependencies**: Uses only Python standard library
- **Fast validation**: Efficient lexer and parser implementation
- **Detailed errors**: Precise error messages with location information
- **Extensible**: Clean API for integration into other tools
- **Well-tested**: Comprehensive test suite with real-world queries

### Python Support
- Python 3.7+
- Cross-platform (Windows, macOS, Linux)