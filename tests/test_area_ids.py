#!/usr/bin/env python3
"""
Test script to debug area with multiple IDs
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_area_multiple_ids():
    """Test area with multiple IDs."""

    checker = OverpassQLSyntaxChecker()

    test_queries = [
        # Single ID (should work)
        "area(id:3600058437);out;",
        # Multiple IDs (the problematic case)
        "area(id:3600058437,3600058446,3600058447);out;",
        # The actual problematic query from the file
        (
            "[maxsize:2073741824];area(id:3600058437,3600058446,3600058447);"
            'way["highway"~"pedestrian|service|residential|track"]'
            '["highway_authority_ref"];out count;out tags;out center;'
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
    test_area_multiple_ids()
