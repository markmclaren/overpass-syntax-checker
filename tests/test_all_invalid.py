#!/usr/bin/env python3
"""Test all invalid queries to see improvement."""

import os
import sys

from overpass_ql_checker.checker import OverpassQLSyntaxChecker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def main():
    """Test all invalid queries and count how many are now valid."""

    checker = OverpassQLSyntaxChecker()

    with open("invalid_queries.txt", "r") as f:
        queries = [line.strip() for line in f if line.strip()]

    print(f"Testing {len(queries)} previously invalid queries...")

    now_valid = 0
    still_invalid = 0

    for i, query in enumerate(queries):
        result = checker.check_syntax(query)
        if result["valid"]:
            now_valid += 1
        else:
            still_invalid += 1

        # Show progress
        if (i + 1) % 50 == 0 or i == len(queries) - 1:
            print(
                f"Processed {i + 1}/{len(queries)} queries... "
                f"Valid: {now_valid}, Invalid: {still_invalid}"
            )

    print("\nResults:")
    print(
        f"  Now valid: {now_valid}/{len(queries)} "
        f"({now_valid / len(queries) * 100:.1f}%)"
    )
    print(
        f"  Still invalid: {still_invalid}/{len(queries)} "
        f"({still_invalid / len(queries) * 100:.1f}%)"
    )

    # Show a few examples of queries that are still invalid
    print("\nSample of queries still invalid:")
    shown = 0
    for query in queries:
        if shown >= 5:
            break
        result = checker.check_syntax(query)
        if not result["valid"]:
            print(f"  {query[:80]}{'...' if len(query) > 80 else ''}")
            shown += 1


if __name__ == "__main__":
    main()
