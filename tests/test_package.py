"""
Tests for the Overpass QL Syntax Checker package.

This file contains comprehensive tests for the overpass-ql-checker library.
Run with: python -m pytest tests/ (after installation)
Or run directly: python tests/test_overpass_checker.py
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

# Add the source directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_simple_valid_queries():
    """Test simple valid queries."""
    checker = OverpassQLSyntaxChecker()
    valid_queries = [
        "node[amenity=restaurant];out;",
        "way[highway=primary];out geom;",
        "rel[type=route][route=bus];out;",
        "[out:json][timeout:25];node[amenity=cafe];out;",
    ]

    for query in valid_queries:
        result = checker.check_syntax(query)
        assert result["valid"], f"Query should be valid: {query}"
        assert len(result["errors"]) == 0, f"No errors expected for: {query}"


def test_simple_invalid_queries():
    """Test simple invalid queries."""
    checker = OverpassQLSyntaxChecker()
    invalid_queries = [
        "node[amenity restaurant];out;",  # Missing equals in tag filter
        "node[;out;",  # Malformed tag filter
        "[bbox:invalid,coords];",  # Invalid bbox coordinates
    ]

    for query in invalid_queries:
        result = checker.check_syntax(query)
        assert not result["valid"], f"Query should be invalid: {query}"
        assert len(result["errors"]) > 0, f"Errors expected for: {query}"


def test_complex_valid_queries():
    """Test complex valid queries."""
    checker = OverpassQLSyntaxChecker()
    complex_queries = [
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
        "node(around:1000,52.5,13.4)[amenity=restaurant];out;",
        'nwr[name~"^Berlin"];out;',
    ]

    for query in complex_queries:
        result = checker.check_syntax(query)
        assert result["valid"], f"Complex query should be valid: {query.strip()}"


def test_settings_validation():
    """Test settings validation."""
    checker = OverpassQLSyntaxChecker()
    valid_settings = [
        "[out:json];",
        "[timeout:25];",
        "[maxsize:1073741824];",
        "[bbox:50.0,7.0,51.0,8.0];",
    ]

    for setting in valid_settings:
        result = checker.check_syntax(setting)
        assert result["valid"], f"Setting should be valid: {setting}"


def test_tag_filters():
    """Test tag filter validation."""
    checker = OverpassQLSyntaxChecker()
    valid_filters = [
        "node[amenity=restaurant];out;",
        'node[name="Test Name"];out;',
        'node[name~"^Test"];out;',
        'node["addr:city"="Berlin"];out;',
        "node[!amenity];out;",
    ]

    for query in valid_filters:
        result = checker.check_syntax(query)
        assert result["valid"], f"Tag filter should be valid: {query}"


def test_spatial_filters():
    """Test spatial filter validation."""
    checker = OverpassQLSyntaxChecker()
    valid_spatial = [
        "node(50.0,7.0,51.0,8.0);out;",  # bbox
        "node(around:1000,52.5,13.4);out;",  # around
        "node(area.searchArea);out;",  # area reference
    ]

    for query in valid_spatial:
        result = checker.check_syntax(query)
        assert result["valid"], f"Spatial filter should be valid: {query}"


def test_union_queries():
    """Test union query validation."""
    checker = OverpassQLSyntaxChecker()
    valid_unions = [
        "(node[amenity=cafe]; way[amenity=cafe];);out;",
        '(node[name="Test"]; - node[historic];);out;',
    ]

    for query in valid_unions:
        result = checker.check_syntax(query)
        assert result["valid"], f"Union query should be valid: {query}"


def test_output_statements():
    """Test output statement validation."""
    checker = OverpassQLSyntaxChecker()
    valid_outputs = [
        "node[amenity=cafe];out;",
        "node[amenity=cafe];out geom;",
        "node[amenity=cafe];out meta;",
        "node[amenity=cafe];out count;",
        "node[amenity=cafe];out ids;",
    ]

    for query in valid_outputs:
        result = checker.check_syntax(query)
        assert result["valid"], f"Output statement should be valid: {query}"


def test_error_reporting():
    """Test that error messages are helpful."""
    checker = OverpassQLSyntaxChecker()
    invalid_query = "node[amenity restaurant];out;"  # Missing equals in tag filter
    result = checker.check_syntax(invalid_query)

    assert not result["valid"]
    assert len(result["errors"]) > 0
    assert any(
        "expected" in error.lower() or "tag" in error.lower()
        for error in result["errors"]
    ), "Error should mention expected token or tag filter issue"


def test_warning_system():
    """Test that warnings are generated appropriately."""
    checker = OverpassQLSyntaxChecker()
    # This would test warnings for deprecated features or potential issues
    # For now, just ensure warnings list is always present
    result = checker.check_syntax("node[amenity=cafe];out;")
    assert "warnings" in result
    assert isinstance(result["warnings"], list)


def test_tokenization():
    """Test that tokenization works correctly."""
    checker = OverpassQLSyntaxChecker()
    simple_query = "node[amenity=cafe];out;"
    result = checker.check_syntax(simple_query)

    assert "tokens" in result
    assert len(result["tokens"]) > 0
    # Should have tokens for: node, [, amenity, =, cafe, ], ;, out, ;, EOF


def run_all_tests():
    """Run all tests and report results."""
    test_functions = [
        test_simple_valid_queries,
        test_simple_invalid_queries,
        test_complex_valid_queries,
        test_settings_validation,
        test_tag_filters,
        test_spatial_filters,
        test_union_queries,
        test_output_statements,
        test_error_reporting,
        test_warning_system,
        test_tokenization,
    ]

    print("Running Overpass QL Checker Tests")
    print("=" * 40)

    passed = 0
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")

    print("-" * 40)
    print(f"Tests passed: {passed}/{len(test_functions)}")
    print(f"Success rate: {passed / len(test_functions) * 100:.1f}%")

    return passed == len(test_functions)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
