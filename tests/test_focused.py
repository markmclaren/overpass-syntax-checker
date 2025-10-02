#!/usr/bin/env python3
"""Focused tests to understand specific parsing issues."""

import os
import sys

from overpass_ql_checker.checker import OverpassQLSyntaxChecker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def check_query(query, description=""):
    """Test a single query and print results."""
    print(f"\n=== Testing: {description} ===")
    print(f"Query: {query}")

    checker = OverpassQLSyntaxChecker()
    result = checker.check_syntax(query)

    print(f"Valid: {result['valid']}")
    if result["errors"]:
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")
    if result["warnings"]:
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")


def main():
    """Test specific problematic patterns."""

    # Test 1: Template bbox with value assignment
    check_query("{{bbox=area:3606195356}}", "Template bbox assignment")

    # Test 2: geocodeArea template
    check_query('{{geocodeArea:"Bernareggio"}}', "geocodeArea template")

    # Test 3: for user() construct
    check_query('for (user()){ make stat "user"=_.val; out; }', "for user() construct")

    # Test 4: CSV output format
    check_query("[out:csv(user,total,nodes,ways,relations)]", "CSV output format")

    # Test 5: Multiple consecutive out statements
    check_query(
        'node[name="test"]; out; out; >;out skel qt;', "Multiple out statements"
    )

    # Test 6: Basic bbox template
    check_query("node({{bbox}})", "Basic bbox template")

    # Test 7: Set variable with underscore
    check_query("nwr._", "Set variable with underscore")

    # Test 8: around with set variable
    check_query("node(around.zentrum:200.0)", "around with set variable")

    # Test 9: Complex filter with if condition
    check_query('nwr(if:is_number(t["capacity"]))', "if condition filter")

    # Test 10: Union with minus operation
    check_query("(.a; - .b;)", "Union with minus operation")


if __name__ == "__main__":
    main()
