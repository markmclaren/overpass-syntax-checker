#!/usr/bin/env python3
"""
Example usage of the Overpass QL Syntax Checker package.

This script demonstrates how to use the overpass-ql-checker package
to validate Overpass QL queries programmatically.

Installation:
    pip install overpass-ql-checker

Basic usage:
    from overpass_ql_checker import OverpassQLSyntaxChecker
    checker = OverpassQLSyntaxChecker()
    result = checker.check_syntax("node[amenity=restaurant];out;")
"""

from overpass_ql_checker import OverpassQLSyntaxChecker
import os
import sys

# For development/testing - add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def main():
    # Create a syntax checker instance
    checker = OverpassQLSyntaxChecker()

    # Example queries to test
    test_queries = [
        # Valid query
        """
        [out:json][timeout:25];
        area[name="Berlin"]->.searchArea;
        (
          node(area.searchArea)[amenity=restaurant];
          way(area.searchArea)[amenity=restaurant];
          relation(area.searchArea)[amenity=restaurant];
        );
        out center;
        """,
        # Another valid query
        """
        [out:json][bbox:52.5,13.3,52.6,13.5];
        node[amenity=cafe][opening_hours];
        out;
        """,
        # Query with syntax error (missing semicolon)
        """
        [out:json]
        node[amenity=restaurant]
        out;
        """,
        # Query with invalid setting
        """
        [out:invalid_format][timeout:25];
        node[amenity=shop];
        out;
        """,
    ]

    print("Overpass QL Syntax Checker - Example Usage")
    print("=" * 60)

    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Testing Query {i} ---")
        print("Query:")
        print(query.strip())
        print("\nValidation Result:")

        # Check syntax with detailed output
        result = checker.check_syntax(query)

        if result["valid"]:
            print("✅ VALID - Query syntax is correct!")
        else:
            print("❌ INVALID - Query has syntax errors!")

        # Print errors if any
        if result["errors"]:
            print("\nErrors found:")
            for error in result["errors"]:
                print(f"  • {error}")

        # Print warnings if any
        if result["warnings"]:
            print("\nWarnings:")
            for warning in result["warnings"]:
                print(f"  ⚠ {warning}")

        print("-" * 60)

    print("\n🧪 Running built-in test suite...")

    # Run the built-in tests using the CLI
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-m", "overpass_ql_checker.cli", "--test"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✅ Built-in tests completed successfully!")
        else:
            print("❌ Some built-in tests failed")
            print(result.stdout)
    except Exception as e:
        print(f"Error running built-in tests: {e}")


if __name__ == "__main__":
    main()
