#!/usr/bin/env python3
"""
Test script to debug logical operators in expressions
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_logical_operators():
    """Test logical operators in conditional expressions."""

    checker = OverpassQLSyntaxChecker()

    test_queries = [
        # Simple conditional (should work)
        'node(if:t["admin_level"]==5);out;',
        # Logical AND operator (failing)
        'node(if:t["admin_level"]>=5&&t["admin_level"]<=11);out;',
        # Logical OR operator (might also fail)
        'node(if:t["highway"]=="primary"||t["highway"]=="secondary");out;',
        # The actual problematic query from the file
        (
            "[out:json][timeout:60];"
            '(relation["admin_level"]["wikidata"]'
            '(if:t["admin_level"]>=5&&t["admin_level"]<=11)'
            "(-37.025032151632,174.48158132019,-36.713017687755,175.04669057312);"
            ");out;>;out skel qt;"
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
        if not result["valid"]:
            print(f"Tokens ({len(tokens)}): {', '.join(tokens[:15])}")
            if len(tokens) > 15:
                print(f"  ... and {len(tokens) - 15} more")


if __name__ == "__main__":
    test_logical_operators()
