#!/usr/bin/env python3
"""
Test script to debug arithmetic operators in expressions
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_arithmetic_operators():
    """Test arithmetic operators in expressions."""

    checker = OverpassQLSyntaxChecker()

    test_queries = [
        # Simple expressions (might work)
        'way["width"];out;',
        # Arithmetic operators (failing)
        '[out:csv("length")];way["highway"];make stat length=sum(length())/1000;out;',
        # Addition operator
        'way["highway"];make stat total=count(nodes)+count(ways);out;',
        # Division operator (from the file)
        (
            '[maxsize:1000000000][out:csv("number","length")];'
            '{{geocodeArea:"Berlin"}}->.searchArea;'
            'way["railway"="subway"](area.searchArea);'
            "make stat number=count(ways),length=sum(length())/1000;out;"
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
        if not result["valid"]:
            tokens = result.get("tokens", [])
            print(f"Tokens ({len(tokens)}): {', '.join(tokens[:15])}")
            if len(tokens) > 15:
                print(f"  ... and {len(tokens) - 15} more")


if __name__ == "__main__":
    test_arithmetic_operators()
