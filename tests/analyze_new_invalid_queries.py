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
        print("This script was used to analyze queries from an external file.")
        print("The analysis results have been incorporated into the test suite.")
        return []


def _categorize_error(error):
    """Categorize an error message by type"""
    if "Expected" in error:
        return "Expected Token"
    elif "Unexpected" in error:
        return "Unexpected Token"
    elif "Invalid" in error:
        return "Invalid Syntax"
    elif "Unknown" in error:
        return "Unknown Element"
    else:
        return "Other Error"


def _process_query_result(result, error_patterns):
    """Process the result of checking a single query"""
    is_valid = result["valid"]
    if is_valid:
        print("  ✓ Current checker considers this VALID")
        return 1, 0  # valid_count, invalid_count
    else:
        print("  ✗ Current checker considers this INVALID")

        # Get detailed error info
        errors = result.get("errors", [])
        if errors:
            for error in errors[:2]:  # Show first 2 errors
                print(f"    Error: {error}")

                error_type = _categorize_error(error)
                if error_type not in error_patterns:
                    error_patterns[error_type] = 0
                error_patterns[error_type] += 1

        return 0, 1  # valid_count, invalid_count


def _print_summary(queries, valid_count, invalid_count, error_patterns):
    """Print the analysis summary"""
    print("\n=== Summary ===")
    print(f"Total queries: {len(queries)}")
    print(f"Currently detected as valid: {valid_count}")
    print(f"Currently detected as invalid: {invalid_count}")

    if error_patterns:
        print("\nError pattern distribution:")
        for pattern, count in sorted(error_patterns.items()):
            print(f"  {pattern}: {count}")


def analyze_invalid_queries():
    """Analyze the invalid queries from invalid_queries_comments.txt"""
    queries = _load_queries()

    if not queries:
        print("No queries to analyze. Exiting.")
        return

    print(f"Found {len(queries)} queries to analyze\n")

    checker = OverpassQLSyntaxChecker()
    valid_count = 0
    invalid_count = 0
    error_patterns = {}

    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query[:80]}{'...' if len(query) > 80 else ''}")

        try:
            result = checker.check_syntax(query)
            v_count, i_count = _process_query_result(result, error_patterns)
            valid_count += v_count
            invalid_count += i_count
        except Exception as e:
            print(f"  ! Exception during validation: {e}")
            invalid_count += 1

        print()

    _print_summary(queries, valid_count, invalid_count, error_patterns)


if __name__ == "__main__":
    analyze_invalid_queries()
