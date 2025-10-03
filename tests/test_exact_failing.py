#!/usr/bin/env python3
"""
Test the exact failing query to understand the issue.
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_exact_failing_query():
    """Test the exact failing query from invalid_queries.txt"""

    checker = OverpassQLSyntaxChecker()

    # The exact failing query from line 4
    query = (
        "nwr[shop=supermarket]({{bbox}})->.all;"
        'for .all (t["name"]){ if (count(nodes)+count(ways)+count(relations) > 10) '
        "{ ( make numerous name=_.val; .result; )->.result; }}"
        'make blacklist list=result.set(t["name"])->.blacklist;'
        'nwr.all(if:!lrs_in(t["name"],blacklist.u(t["list"])));out center;'
    )

    print("Testing exact failing query...")
    print("=" * 80)
    print(f"Query: {query[:100]}...")

    try:
        result = checker.check_syntax(query)
        status = "✅ VALID" if result["valid"] else "❌ INVALID"
        print(f"Status: {status}")
        if not result["valid"]:
            print("Errors:")
            for error in result["errors"]:
                print(f"  {error}")
    except Exception as e:
        print(f"Exception: {e}")

    # Let me try breaking it down into parts
    print("\nTesting parts of the query:")
    parts = [
        "nwr[shop=supermarket]({{bbox}})->.all",
        (
            'for .all (t["name"]){ if (count(nodes)+count(ways)+count(relations) > 10) '
            "{ ( make numerous name=_.val; .result; )->.result; }}"
        ),
        'make blacklist list=result.set(t["name"])->.blacklist',
        'nwr.all(if:!lrs_in(t["name"],blacklist.u(t["list"])))',
        "out center",
    ]

    for i, part in enumerate(parts, 1):
        print(f"\nPart {i}: {part}")
        try:
            result = checker.check_syntax(part)
            status = "✅ VALID" if result["valid"] else "❌ INVALID"
            print(f"  Status: {status}")
            if not result["valid"]:
                for error in result["errors"]:
                    print(f"    Error: {error}")
        except Exception as e:
            print(f"    Exception: {e}")


if __name__ == "__main__":
    test_exact_failing_query()
