#!/usr/bin/env python3
"""
Script to categorize the remaining invalid queries by error type
and identify which ones can be easily fixed vs need parser improvements.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from overpass_ql_checker import OverpassQLSyntaxChecker


def categorize_errors():
    """Categorize all remaining invalid queries by error type."""

    # Read the invalid queries
    with open("invalid_queries.txt", "r", encoding="utf-8") as f:
        queries = [line.strip() for line in f if line.strip()]

    checker = OverpassQLSyntaxChecker()

    categories = {
        "missing_semicolon": [],
        "missing_parenthesis": [],
        "template_placeholders": [],
        "pbf_format": [],
        "date_format": [],
        "set_operations": [],
        "complex_filters": [],
        "other": [],
    }

    print(f"Categorizing {len(queries)} invalid queries...")
    print("=" * 80)

    for i, query in enumerate(queries):
        result = checker.check_syntax(query)

        if result["valid"]:
            print(f"Query {i+1}: Actually VALID (false positive)")
            continue

        errors = result["errors"]
        error_text = " ".join(errors)

        # Categorize based on error patterns
        categorized = False

        # Template placeholders ({{bbox}}, {{center}}, etc.)
        if "{{" in query and (
            "Expected latitude" in error_text or "Expected longitude" in error_text
        ):
            categories["template_placeholders"].append((i + 1, query, errors))
            categorized = True

        # Missing semicolons
        elif "Expected ;" in error_text and not categorized:
            categories["missing_semicolon"].append((i + 1, query, errors))
            categorized = True

        # Missing parentheses
        elif "Expected )" in error_text and not categorized:
            categories["missing_parenthesis"].append((i + 1, query, errors))
            categorized = True

        # PBF format
        elif "Invalid output format: pbf" in error_text:
            categories["pbf_format"].append((i + 1, query, errors))
            categorized = True

        # Date format issues
        elif "Invalid date format" in error_text:
            categories["date_format"].append((i + 1, query, errors))
            categorized = True

        # Set operations (variable names, map_to_area, etc.)
        elif any(
            phrase in error_text
            for phrase in ["Expected set name", "map_to_area", "convert"]
        ):
            categories["set_operations"].append((i + 1, query, errors))
            categorized = True

        # Complex filter issues
        elif any(
            phrase in error_text
            for phrase in ["Expected }", "if:", "version()", "user:"]
        ):
            categories["complex_filters"].append((i + 1, query, errors))
            categorized = True

        # Everything else
        if not categorized:
            categories["other"].append((i + 1, query, errors))

    # Print summary
    print("\nCATEGORY SUMMARY:")
    print("=" * 80)
    total = 0
    for category, items in categories.items():
        count = len(items)
        total += count
        if count > 0:
            print(f"{category.replace('_', ' ').title()}: {count} queries")

    print(f"\nTotal categorized: {total}")

    # Print details for each category
    for category, items in categories.items():
        if not items:
            continue

        print(
            f"\n{'='*20} {category.replace('_', ' ').upper()} ({len(items)} queries) {'='*20}"
        )

        for query_num, query, errors in items[:5]:  # Show first 5 of each category
            print(f"\nQuery {query_num}:")
            print(f"  Text: {query[:100]}{'...' if len(query) > 100 else ''}")
            print(f"  Errors: {errors[0] if errors else 'No errors listed'}")

        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more")

    return categories


if __name__ == "__main__":
    categorize_errors()
