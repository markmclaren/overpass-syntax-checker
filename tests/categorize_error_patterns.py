#!/usr/bin/env python3

import os
import sys

from overpass_ql_checker.checker import OverpassQLSyntaxChecker

# Add the src directory to Python path to import the checker
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def _load_queries():
    """Load queries from the invalid_queries_comments.txt file if it exists"""
    queries_file = os.path.join(
        os.path.dirname(__file__), "..", "invalid_queries_comments.txt"
    )

    try:
        with open(queries_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"File {queries_file} not found.")
        print("This script was used to categorize errors from an external file.")
        print("The categorization results have been incorporated into the test suite.")
        return []


def _categorize_error(error, error_categories, i, query):
    """Categorize a single error and add it to the appropriate category"""
    error_lower = error.lower()

    if "unexpected token: ->" in error_lower or "expected ), got ." in error_lower:
        error_categories["arrow_operator"].append((i, query, error))
        print(f"  → ARROW OPERATOR: {error}")
    elif "invalid output format" in error_lower:
        error_categories["output_format"].append((i, query, error))
        print(f"  → OUTPUT FORMAT: {error}")
    elif "invalid date format" in error_lower:
        error_categories["date_format"].append((i, query, error))
        print(f"  → DATE FORMAT: {error}")
    elif "expected set name after" in error_lower:
        error_categories["set_names"].append((i, query, error))
        print(f"  → SET NAMES: {error}")
    elif "foreach" in error_lower:
        error_categories["foreach_loops"].append((i, query, error))
        print(f"  → FOREACH: {error}")
    elif "expected area parameter" in error_lower:
        error_categories["area_parameters"].append((i, query, error))
        print(f"  → AREA PARAM: {error}")
    elif "convert" in error_lower:
        error_categories["convert_statement"].append((i, query, error))
        print(f"  → CONVERT: {error}")
    else:
        error_categories["other"].append((i, query, error))
        print(f"  → OTHER: {error}")


def _print_category_summary(error_categories):
    """Print summary of error categories"""
    print("\n" + "=" * 60)
    print("ERROR CATEGORY SUMMARY")
    print("=" * 60)

    for category, errors in error_categories.items():
        if errors:
            print(f"\n{category.upper().replace('_', ' ')} ({len(errors)} queries):")
            for query_num, query, error in errors:
                print(f"  Query {query_num}: {error}")


def _print_improvement_analysis(error_categories):
    """Print analysis of potential improvements needed"""
    print("\n" + "=" * 60)
    print("POTENTIAL IMPROVEMENTS NEEDED")
    print("=" * 60)

    if error_categories["arrow_operator"]:
        count = len(error_categories["arrow_operator"])
        print(f"\n• Arrow operator parsing ({count} cases)")
        print(
            "  Many queries use complex arrow syntax that might be valid "
            "in real Overpass QL"
        )

    if error_categories["output_format"]:
        count = len(error_categories["output_format"])
        print(f"\n• Output format support ({count} cases)")
        print("  Missing support for: osm, xlsx, pjsonl formats")

    if error_categories["date_format"]:
        count = len(error_categories["date_format"])
        print(f"\n• Date format parsing ({count} cases)")
        print("  Missing support for timezone suffixes like +09:00")

    if error_categories["set_names"]:
        count = len(error_categories["set_names"])
        print(f"\n• Set name handling ({count} cases)")
        print("  Issues with foreach loops and set operations")

    if error_categories["area_parameters"]:
        count = len(error_categories["area_parameters"])
        print(f"\n• Area parameter parsing ({count} cases)")
        print("  Issues with complex area expressions")


def categorize_invalid_query_errors():
    """Categorize the specific types of errors in the invalid queries"""
    queries = _load_queries()

    if not queries:
        print("No queries to analyze. Exiting.")
        return

    print(f"Analyzing error patterns in {len(queries)} invalid queries\n")

    checker = OverpassQLSyntaxChecker()

    # Categories of errors we'll track
    error_categories = {
        "arrow_operator": [],  # Issues with -> operator
        "output_format": [],  # Invalid output formats
        "date_format": [],  # Date format issues
        "set_names": [],  # Set name parsing issues
        "foreach_loops": [],  # Issues with foreach syntax
        "area_parameters": [],  # Area parameter issues
        "convert_statement": [],  # Issues with convert statements
        "other": [],  # Other unclassified errors
    }

    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}:")
        print(f"  {query[:100]}{'...' if len(query) > 100 else ''}")

        result = checker.check_syntax(query)
        errors = result.get("errors", [])

        for error in errors[:1]:  # Look at first error for categorization
            _categorize_error(error, error_categories, i, query)

    _print_category_summary(error_categories)
    _print_improvement_analysis(error_categories)


if __name__ == "__main__":
    categorize_invalid_query_errors()
