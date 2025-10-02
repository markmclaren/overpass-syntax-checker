#!/usr/bin/env python3
"""
Script to analyze overall improvement in the invalid queries
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from overpass_ql_checker import OverpassQLSyntaxChecker


def analyze_overall_improvement():
    """Analyze the overall improvement in query validation."""

    # Read the invalid queries
    with open("invalid_queries.txt", "r", encoding="utf-8") as f:
        queries = [line.strip() for line in f if line.strip()]

    checker = OverpassQLSyntaxChecker()

    print(f"Analyzing ALL {len(queries)} queries from invalid_queries.txt")
    print("=" * 80)

    valid_count = 0
    invalid_count = 0

    for i, query in enumerate(queries):
        result = checker.check_syntax(query)

        if result["valid"]:
            valid_count += 1
        else:
            invalid_count += 1

        # Show progress every 50 queries
        if (i + 1) % 50 == 0:
            print(
                f"Processed {i + 1}/{len(queries)} queries. "
                f"Valid: {valid_count}, Invalid: {invalid_count}"
            )

    print("\n" + "=" * 80)
    print("FINAL RESULTS:")
    print(f"Total queries: {len(queries)}")
    print(f"Now valid: {valid_count} ({valid_count/len(queries)*100:.1f}%)")
    print(f"Still invalid: {invalid_count} ({invalid_count/len(queries)*100:.1f}%)")
    print(
        f"Improvement: {valid_count} queries that were previously invalid "
        f"are now valid!"
    )


if __name__ == "__main__":
    analyze_overall_improvement()
