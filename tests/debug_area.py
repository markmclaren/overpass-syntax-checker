#!/usr/bin/env python3
"""Debug specific area parsing issue."""

import os
import sys

from overpass_ql_checker.checker import OverpassQLSyntaxChecker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_query(query, description=""):
    """Test a single query and print results."""
    print(f"\n=== Testing: {description} ===")
    print(f"Query: {query}")

    checker = OverpassQLSyntaxChecker()
    result = checker.check_syntax(query)

    print(f"Valid: {result['valid']}")
    if result["errors"]:
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")


def main():
    """Debug the area parsing issue."""

    # Break down the problematic query
    test_query("area[name=Portugal]", "Simple area query")
    test_query('area[admin_level=2][name="Portugal"]', "Area with two filters")
    test_query('nwr["waterway"](area)', "Query with area reference")


if __name__ == "__main__":
    main()
