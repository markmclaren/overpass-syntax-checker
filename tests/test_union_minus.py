#!/usr/bin/env python3
"""
Test script to analyze the union minus operation syntax issue.
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_union_minus():
    """Test union minus operations that are currently failing."""

    checker = OverpassQLSyntaxChecker()

    # Simplified versions of the failing queries
    test_queries = [
        # Basic union with minus operation
        "(way[amenity=restaurant]; - .water)",
        # Union with assignment after
        "(way[amenity=restaurant]; - .water)->.result",
        # The problematic syntax from query 1
        (
            '( way["addr:street"~"^(Thistle Drive)$"]; '
            'way["addr:street"~"^(Argyll Place)$"]; );._->.a'
        ),
        # Alternative correct syntax
        (
            '( way["addr:street"~"^(Thistle Drive)$"]; '
            'way["addr:street"~"^(Argyll Place)$"]; )._->.a'
        ),
        # Another alternative
        (
            '( way["addr:street"~"^(Thistle Drive)$"]; '
            'way["addr:street"~"^(Argyll Place)$"]; )->.temp; .temp->.a'
        ),
        # Test difference operation with set
        "( way[amenity=restaurant]; - .water; )",
        # Simple case
        "(.a; - .b)",
    ]

    print("Testing union minus operations...")
    print("=" * 60)

    for i, query in enumerate(test_queries, 1):
        try:
            result = checker.check_syntax(query)
            status = "✅ VALID" if result["valid"] else "❌ INVALID"
            print(f"Query {i}: {status}")
            print(f"  {query}")
            if not result["valid"]:
                for error in result["errors"]:
                    print(f"  Error: {error}")
            print()
        except Exception as e:
            print(f"Query {i}: 💥 EXCEPTION")
            print(f"  {query}")
            print(f"  Exception: {e}")
            print()


if __name__ == "__main__":
    test_union_minus()
