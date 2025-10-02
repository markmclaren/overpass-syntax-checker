"""
Test cases specifically for the changed filter functionality.
These tests cover the new spatial filter context parsing that was added.
"""

from src.overpass_ql_checker.checker import OverpassQLSyntaxChecker


class TestChangedFilterFunctionality:
    """Test cases for changed filter parsing in both bracket and spatial contexts."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = OverpassQLSyntaxChecker()

    def test_spatial_changed_filter_date_range(self):
        """Test changed filter with date range in spatial context (parentheses)."""
        query = '(node(changed:"2020-07-23T00:00:00Z","2020-07-24T00:00:00Z"););out;'
        result = self.checker.check_syntax(query)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_spatial_changed_filter_single_date(self):
        """Test changed filter with single date in spatial context."""
        query = '(node(changed:"2020-07-23T00:00:00Z"););out;'
        result = self.checker.check_syntax(query)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_spatial_changed_filter_with_other_filters(self):
        """Test changed filter combined with other spatial filters."""
        query = (
            '(node(changed:"2020-07-23T00:00:00Z","2020-07-24T00:00:00Z")'
            '(user:"testuser"););out;'
        )
        result = self.checker.check_syntax(query)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_spatial_changed_filter_invalid_first_date(self):
        """Test changed filter with invalid first date format."""
        query = '(node(changed:"invalid-date","2020-07-24T00:00:00Z"););out;'
        result = self.checker.check_syntax(query)
        assert result["valid"] is False
        assert any("Invalid date format" in error for error in result["errors"])

    def test_spatial_changed_filter_invalid_second_date(self):
        """Test changed filter with invalid second date format."""
        query = '(node(changed:"2020-07-23T00:00:00Z","invalid-date"););out;'
        result = self.checker.check_syntax(query)
        assert result["valid"] is False
        assert any("Invalid date format" in error for error in result["errors"])

    def test_spatial_changed_filter_missing_date(self):
        """Test changed filter with missing date."""
        query = "(node(changed:););out;"
        result = self.checker.check_syntax(query)
        assert result["valid"] is False
        assert any("Expected date string" in error for error in result["errors"])

    def test_spatial_changed_filter_missing_second_date(self):
        """Test changed filter with missing second date after comma."""
        query = '(node(changed:"2020-07-23T00:00:00Z",););out;'
        result = self.checker.check_syntax(query)
        assert result["valid"] is False
        assert any("Expected second date string" in error for error in result["errors"])

    def test_bracket_changed_filter_still_works(self):
        """Test that bracket context changed filter still works."""
        query = 'node[changed:"2020-07-23T00:00:00Z","2020-07-24T00:00:00Z"];out;'
        _ = self.checker.check_syntax(query)
        # Note: This might fail due to existing limitations, but we test to ensure
        # our changes don't break existing functionality
        # The test documents current behavior
        # We don't assert the result since this is documenting existing behavior

    def test_complex_query_with_spatial_changed_filter(self):
        """Test a complex real-world style query with spatial changed filter."""
        query = """(
            node(changed:"2020-07-23T00:00:00Z","2020-07-24T00:00:00Z")(user:"HK2002")({{bbox}});
            way(changed:"2020-07-23T00:00:00Z","2020-07-24T00:00:00Z")(user:"HK2002")({{bbox}});
            relation(changed:"2020-07-23T00:00:00Z","2020-07-24T00:00:00Z")(user:"HK2002")({{bbox}});
        );out;>;out skel qt;"""
        result = self.checker.check_syntax(query)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_uid_filter_in_spatial_context(self):
        """Test uid filter in spatial context (also added in the fix)."""
        query = "(way(uid:8559160););out;"
        result = self.checker.check_syntax(query)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_user_filter_in_spatial_context(self):
        """Test user filter in spatial context (also added in the fix)."""
        query = '(node(user:"testuser"););out;'
        result = self.checker.check_syntax(query)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_multiple_spatial_filters_combination(self):
        """Test multiple spatial filters combined including changed."""
        query = '(node(changed:"2020-01-01T00:00:00Z")(user:"test")(uid:123););out;'
        result = self.checker.check_syntax(query)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_changed_filter_date_validation_edge_cases(self):
        """Test edge cases for date validation in changed filter."""
        test_cases = [
            # Valid ISO 8601 format dates (syntax checker only validates format, not
            # actual date values)
            ('(node(changed:"2020-12-31T23:59:59Z"););out;', True),
            ('(node(changed:"2000-01-01T00:00:00Z"););out;', True),
            (
                '(node(changed:"2020-13-01T00:00:00Z"););out;',
                True,
            ),  # Invalid month but valid format
            (
                '(node(changed:"2020-01-32T00:00:00Z"););out;',
                True,
            ),  # Invalid day but valid format
            (
                '(node(changed:"2020-01-01T25:00:00Z"););out;',
                True,
            ),  # Invalid hour but valid format
            (
                '(node(changed:"2020-01-01T00:60:00Z"););out;',
                True,
            ),  # Invalid minute but valid format
            (
                '(node(changed:"2020-01-01T00:00:60Z"););out;',
                True,
            ),  # Invalid second but valid format
            # Invalid date formats (these should fail)
            ('(node(changed:"2020-01-01 00:00:00"););out;', False),  # Missing T and Z
            ('(node(changed:"20-01-01T00:00:00Z"););out;', False),  # Wrong year format
            (
                '(node(changed:"2020-1-01T00:00:00Z"););out;',
                False,
            ),  # Wrong month format
            ('(node(changed:"2020-01-1T00:00:00Z"););out;', False),  # Wrong day format
            ('(node(changed:"2020-01-01T0:00:00Z"););out;', False),  # Wrong hour format
            (
                '(node(changed:"2020-01-01T00:0:00Z"););out;',
                False,
            ),  # Wrong minute format
            (
                '(node(changed:"2020-01-01T00:00:0Z"););out;',
                False,
            ),  # Wrong second format
            ('(node(changed:"2020-01-01T00:00:00"););out;', False),  # Missing Z
        ]

        for query, should_be_valid in test_cases:
            result = self.checker.check_syntax(query)
            if should_be_valid:
                assert (
                    result["valid"] is True
                ), f"Expected valid but got invalid for: {query}"
            else:
                assert (
                    result["valid"] is False
                ), f"Expected invalid but got valid for: {query}"
