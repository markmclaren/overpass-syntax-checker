"""
Tests for the Overpass QL Syntax Checker package.

This file contains comprehensive tests for the overpass-ql-checker library.
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

# Add the source directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestOverpassQLSyntaxChecker:
    """Test suite for the OverpassQLSyntaxChecker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = OverpassQLSyntaxChecker()

    def test_simple_valid_queries(self):
        """Test simple valid queries."""
        valid_queries = [
            "node[amenity=restaurant];out;",
            "way[highway=primary];out geom;",
            "rel[type=route][route=bus];out;",
            "[out:json][timeout:25];node[amenity=cafe];out;",
        ]

        for query in valid_queries:
            result = self.checker.check_syntax(query)
            assert result["valid"], f"Query should be valid: {query}"
            assert len(result["errors"]) == 0, f"No errors expected for: {query}"

    def test_simple_invalid_queries(self):
        """Test simple invalid queries."""
        invalid_queries = [
            "node[amenity restaurant];out;",  # Missing equals in tag filter
            "node[;out;",  # Malformed tag filter
            "way[highway=primary](invalid);out;",  # Invalid spatial filter
        ]

        for query in invalid_queries:
            result = self.checker.check_syntax(query)
            assert not result["valid"], f"Query should be invalid: {query}"
            assert len(result["errors"]) > 0, f"Errors expected for: {query}"

    def test_unknown_settings_as_warnings(self):
        """Test that unknown settings generate warnings, not errors."""
        query = "[invalid:setting];"
        result = self.checker.check_syntax(query)
        assert result["valid"], f"Query with unknown setting should be valid: {query}"
        assert (
            len(result["warnings"]) > 0
        ), f"Warnings expected for unknown setting: {query}"
        assert any(
            "Unknown setting" in warning for warning in result["warnings"]
        ), f"Expected 'Unknown setting' warning: {result['warnings']}"

    def test_complex_valid_queries(self):
        """Test complex valid queries."""
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
            """
            [out:json][timeout:60];
            (
              node[amenity=pub]({{bbox}});
              way[amenity=pub]({{bbox}});
              rel[amenity=pub]({{bbox}});
            );
            out geom;
            """,
            "node(around:1000,52.5,13.4)[amenity=restaurant];out;",
            'nwr[name~"^Berlin"];out;',
        ]

        for query in complex_queries:
            result = self.checker.check_syntax(query)
            assert result["valid"], f"Complex query should be valid: {query.strip()}"

    def test_settings_validation(self):
        """Test settings validation."""
        valid_settings = [
            "[out:json];",
            "[timeout:25];",
            "[maxsize:1073741824];",
            "[bbox:50.0,7.0,51.0,8.0];",
        ]

        for setting in valid_settings:
            result = self.checker.check_syntax(setting)
            assert result["valid"], f"Setting should be valid: {setting}"

    def test_tag_filters(self):
        """Test tag filter validation."""
        valid_filters = [
            "node[amenity=restaurant];out;",
            'node[name="Test Name"];out;',
            'node[name~"^Test"];out;',
            'node["addr:city"="Berlin"];out;',
            "node[!amenity];out;",
        ]

        for query in valid_filters:
            result = self.checker.check_syntax(query)
            assert result["valid"], f"Tag filter should be valid: {query}"

    def test_spatial_filters(self):
        """Test spatial filter validation."""
        valid_spatial = [
            "node(50.0,7.0,51.0,8.0);out;",  # bbox
            "node(around:1000,52.5,13.4);out;",  # around
            "node(area.searchArea);out;",  # area reference
        ]

        for query in valid_spatial:
            result = self.checker.check_syntax(query)
            assert result["valid"], f"Spatial filter should be valid: {query}"

    def test_union_queries(self):
        """Test union query validation."""
        valid_unions = [
            "(node[amenity=cafe]; way[amenity=cafe];);out;",
            '(node[name="Test"]; - node[historic];);out;',
        ]

        for query in valid_unions:
            result = self.checker.check_syntax(query)
            assert result["valid"], f"Union query should be valid: {query}"

    def test_output_statements(self):
        """Test output statement validation."""
        valid_outputs = [
            "node[amenity=cafe];out;",
            "node[amenity=cafe];out geom;",
            "node[amenity=cafe];out meta;",
            "node[amenity=cafe];out count;",
            "node[amenity=cafe];out ids;",
        ]

        for query in valid_outputs:
            result = self.checker.check_syntax(query)
            assert result["valid"], f"Output statement should be valid: {query}"

    def test_error_reporting(self):
        """Test that error messages are helpful."""
        invalid_query = "node[amenity restaurant];out;"  # Missing equals in tag filter
        result = self.checker.check_syntax(invalid_query)

        assert not result["valid"]
        assert len(result["errors"]) > 0
        assert any(
            "expected" in error.lower() or "tag" in error.lower()
            for error in result["errors"]
        ), "Error should mention expected token or tag filter issue"

    def test_warning_system(self):
        """Test that warnings are generated appropriately."""
        # This would test warnings for deprecated features or potential issues
        # For now, just ensure warnings list is always present
        result = self.checker.check_syntax("node[amenity=cafe];out;")
        assert "warnings" in result
        assert isinstance(result["warnings"], list)

    def test_tokenization(self):
        """Test that tokenization works correctly."""
        simple_query = "node[amenity=cafe];out;"
        result = self.checker.check_syntax(simple_query)

        assert "tokens" in result
        assert len(result["tokens"]) > 0
        # Should have tokens for: node, [, amenity, =, cafe, ], ;, out, ;, EOF


if __name__ == "__main__":
    # Run tests directly
    test_instance = TestOverpassQLSyntaxChecker()
    test_instance.setup_method()

    # Run basic tests
    test_methods = [
        test_instance.test_simple_valid_queries,
        test_instance.test_simple_invalid_queries,
        test_instance.test_settings_validation,
        test_instance.test_tag_filters,
        test_instance.test_spatial_filters,
        test_instance.test_union_queries,
        test_instance.test_output_statements,
        test_instance.test_error_reporting,
        test_instance.test_warning_system,
        test_instance.test_tokenization,
    ]

    passed = 0
    for test_method in test_methods:
        try:
            test_method()
            print(f"✓ {test_method.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_method.__name__}: {e}")

    print(f"\nTests passed: {passed}/{len(test_methods)}")
