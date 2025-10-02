"""
Command-line interface for the Overpass QL Syntax Checker.

This module provides the command-line interface functionality for the
overpass-ql-checker package.
"""

import argparse
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .checker import OverpassQLSyntaxChecker
else:
    from overpass_ql_checker.checker import OverpassQLSyntaxChecker


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Overpass QL Syntax Checker",
        epilog="Examples:\n"
        '  overpass-ql-check "node[amenity=restaurant];out;"\n'
        "  overpass-ql-check -f my_query.overpass",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", nargs="?", help="Query string to check")
    parser.add_argument("-f", "--file", help="File containing query to check")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print detailed information including tokens",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    args = parser.parse_args()

    checker = OverpassQLSyntaxChecker()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                query = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    elif args.query:
        query = args.query
    else:
        print("Error: Please provide a query string or file.")
        parser.print_help()
        sys.exit(1)

    is_valid = checker.validate_query(query, verbose=args.verbose)
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
