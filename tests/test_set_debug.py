#!/usr/bin/env python3

import os
import sys

from overpass_ql_checker.checker import OverpassQLSyntaxChecker

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


def test_set_operations():
    """Test set operations specifically."""

    # Simplified set operations queries
    test_queries = [
        # Simple set intersection
        "node.me.julian;out;",
        # Simple set difference
        "(.b; - .a;)->.diff;",
        # Set assignment with diff
        "(.c; - .b;)->.diff;.diff out;",
        # Just the diff assignment part
        "->.diff;",
    ]

    checker = OverpassQLSyntaxChecker()

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 40}")
        print(f"Test {i}: {query}")
        print(f"{'=' * 40}")

        result = checker.check_syntax(query)
        print(f"Valid: {result['valid']}")

        if result["errors"]:
            print("Errors:")
            for error in result["errors"]:
                print(f"  - {error}")

        # Show first few tokens for debugging
        if result["tokens"]:
            print(f"First few tokens: {result['tokens'][:10]}")


if __name__ == "__main__":
    test_set_operations()
