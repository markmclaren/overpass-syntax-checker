#!/usr/bin/env python3
"""
Test script to debug role-based filtering syntax
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_role_filtering():
    """Test role-based filtering syntax."""

    checker = OverpassQLSyntaxChecker()

    test_queries = [
        # Simple relation reference (should work)
        "way(r.M1);out;",
        # Role-based filtering (the problematic cases)
        'way(r.M1:"");out;',
        'node(r.M1:"stop");out;',
        'node(r.M1:"stop_exit_only");out;',
        # The actual problematic query from the file
        (
            "[out:json][timeout:25];(relation(123784);)->.M1;"
            '(way(r.M1:"");node(r.M1:"stop");node(r.M1:"stop_exit_only");'
            'node(r.M1:"stop_entry_only"););out geom;'
        ),
    ]

    for i, query in enumerate(test_queries):
        print(f"\n--- Test {i + 1} ---")
        print(f"Query: {query[:80]}{'...' if len(query) > 80 else ''}")

        result = checker.check_syntax(query)

        if result["valid"]:
            print("✅ VALID")
        else:
            print("❌ INVALID")
            for error in result["errors"][:3]:  # First 3 errors
                print(f"  Error: {error}")

        # Show tokens for debugging
        tokens = result.get("tokens", [])
        print(f"Tokens ({len(tokens)}): {', '.join(tokens[:10])}")
        if len(tokens) > 10:
            print(f"  ... and {len(tokens) - 10} more")


if __name__ == "__main__":
    test_role_filtering()
