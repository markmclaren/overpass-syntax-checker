#!/usr/bin/env python3
"""
Script to analyze the invalid queries from invalid_queries.txt
to understand why they're being flagged as invalid.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from overpass_ql_checker import OverpassQLSyntaxChecker


def analyze_queries():
    """Analyze the invalid queries to understand the issues."""

    # Read the invalid queries
    with open("invalid_queries.txt", "r", encoding="utf-8") as f:
        queries = [line.strip() for line in f if line.strip()]

    checker = OverpassQLSyntaxChecker()

    print(f"Analyzing {len(queries)} queries from invalid_queries.txt")
    print("=" * 80)

    error_patterns = {}

    for i, query in enumerate(queries[:30]):  # Analyze first 30 queries
        print(f"\n--- Query {i+1} ---")
        print(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")

        result = checker.check_syntax(query)

        if result["valid"]:
            print("✅ Actually VALID (false positive)")
        else:
            print("❌ INVALID")
            for error in result["errors"]:
                print(f"  Error: {error}")

                # Extract error type for pattern analysis
                if ":" in error:
                    error_type = error.split(":", 1)[1].split(",")[0].strip()
                    error_patterns[error_type] = error_patterns.get(error_type, 0) + 1

    print("\n" + "=" * 80)
    print("ERROR PATTERN SUMMARY:")
    for pattern, count in sorted(
        error_patterns.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {count:2d}x: {pattern}")


if __name__ == "__main__":
    analyze_queries()
