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


def run_tests(checker: "OverpassQLSyntaxChecker"):
    """Run built-in tests."""
    test_queries = [
        # Valid queries
        ("[out:json][timeout:25];", True, "Settings only"),
        ("node[amenity=restaurant];out;", True, "Simple node query"),
        ("way[highway=primary];out geom;", True, "Way query with geom"),
        ('(node[name="Test"]; way[name="Test"];);out;', True, "Union query"),
        ("node[amenity=shop](50.0,7.0,51.0,8.0);out;", True, "Query with bbox"),
        (
            'area[name="Berlin"]->.a; node(area.a)[amenity=cafe];out;',
            True,
            "Area query with assignment",
        ),
        ("rel[type=route][route=bus];out;", True, "Relation query"),
        ("node(around:1000,52.5,13.4)[amenity=restaurant];out;", True, "Around filter"),
        ('nwr[name~"^Berlin"];out;', True, "Regex filter"),
        ('node["addr:city"="Berlin"];out;', True, "Quoted key with colon"),
        # Invalid queries
        ("node[amenity=restaurant]", False, "Missing semicolon"),
        ("[invalid:setting];", False, "Invalid setting"),
        ("node[;out;", False, "Malformed tag filter"),
        ("way[highway=primary](invalid);out;", False, "Invalid spatial filter"),
        ("node[amenity restaurant];out;", False, "Missing equals in tag filter"),
        ("[bbox:invalid,coords];", False, "Invalid bbox coordinates"),
        ('node[name~"[invalid"];out;', False, "Invalid regex pattern"),
        ("out invalid_mode;", False, "Invalid out mode"),
        ('(node[name="Test"];', False, "Unclosed union"),
        ("node[amenity=shop]->;out;", False, "Invalid assignment syntax"),
    ]

    print("Running Overpass QL Syntax Checker Tests")
    print("=" * 50)

    passed = 0
    total = len(test_queries)

    for i, (query, expected_valid, description) in enumerate(test_queries, 1):
        result = checker.check_syntax(query)
        actual_valid = result["valid"]

        status = "PASS" if actual_valid == expected_valid else "FAIL"
        print(f"Test {i:2d}: {status} - {description}")

        if actual_valid != expected_valid:
            print(f"         Expected: {'VALID' if expected_valid else 'INVALID'}")
            print(f"         Actual:   {'VALID' if actual_valid else 'INVALID'}")
            if result["errors"]:
                print(f"         Errors: {result['errors']}")

        if actual_valid == expected_valid:
            passed += 1

    print("-" * 50)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed / total * 100:.1f}%")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Overpass QL Syntax Checker",
        epilog="Examples:\n"
        '  overpass-ql-check "node[amenity=restaurant];out;"\n'
        "  overpass-ql-check -f my_query.overpass\n"
        "  overpass-ql-check --test",
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
    parser.add_argument("--test", action="store_true", help="Run built-in tests")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    args = parser.parse_args()

    checker = OverpassQLSyntaxChecker()

    if args.test:
        run_tests(checker)
        return

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
