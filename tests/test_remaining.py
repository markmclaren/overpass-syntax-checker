#!/usr/bin/env python3
"""Test specific remaining issues."""

import os
import sys

from overpass_ql_checker.checker import OverpassQLSyntaxChecker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def check_query(query, description=""):
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
    """Test specific remaining issues."""

    # Test 1: Set filter chaining
    check_query('nwr._(if:is_number(t["capacity"]))', "Set filter chaining")

    # Test 2: Template assignment to set
    check_query('{{geocodeArea:"Bernareggio"}}->.area', "Template assignment to set")

    # Test 3: Area query with filters
    check_query(
        'area["admin_level"="8"]["name"="Alfortville"]', "Area with multiple filters"
    )

    # Test 4: Simple area to set assignment
    check_query('area["admin_level"="8"]->.a', "Area to set assignment")

    # Test 5: Multiple settings in one block
    check_query(
        "[out:csv(user,total,nodes,ways,relations)][timeout:25]", "Multiple settings"
    )


if __name__ == "__main__":
    main()
