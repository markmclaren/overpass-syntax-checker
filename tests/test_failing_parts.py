#!/usr/bin/env python3
"""Test specific failing parts."""

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
    """Test specific failing parts."""

    # Test the CSV query components
    check_query(
        (
            'for (user()){ make stat "user"=_.val, nodes=count(nodes), '
            "ways=count(ways), relations=count(relations), "
            "total = count(nodes) + count(ways) + count(relations); out;}"
        ),
        "Complex for loop",
    )

    # Test area filter with spatial reference
    check_query('nwr["amenity"="bicycle_parking"](area.a)', "area spatial filter")

    # Test the specific failing part
    check_query('nwr._(if:is_number(t["capacity"]))', "filter on set with underscore")


if __name__ == "__main__":
    main()
