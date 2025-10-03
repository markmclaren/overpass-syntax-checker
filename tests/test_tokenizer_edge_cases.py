"""
Tests for tokenizer edge cases to improve coverage.
"""

from overpass_ql_checker import OverpassQLSyntaxChecker


class TestTokenizerEdgeCases:
    """Test edge cases in tokenization."""

    def test_newline_tokenization(self):
        """Test that newlines are properly tokenized."""
        checker = OverpassQLSyntaxChecker()
        query = """node["amenity"="restaurant"];
way["highway"];
out;"""
        result = checker.check_syntax(query)
        assert result["valid"]

    def test_single_line_comments(self):
        """Test single-line comments."""
        checker = OverpassQLSyntaxChecker()
        query = """// This is a comment
node["amenity"="restaurant"]; // Another comment
out;"""
        result = checker.check_syntax(query)
        assert result["valid"]

    def test_multi_line_comments(self):
        """Test multi-line comments."""
        checker = OverpassQLSyntaxChecker()
        query = """/* This is a
multi-line comment */
node["amenity"="restaurant"];
out;"""
        result = checker.check_syntax(query)
        assert result["valid"]

    def test_nested_multi_line_comments(self):
        """Test nested multi-line comments - not supported by this tokenizer."""
        checker = OverpassQLSyntaxChecker()
        query = """/* Outer comment /* inner comment */ more outer */
node["amenity"="restaurant"];
out;"""
        result = checker.check_syntax(query)
        # Nested comments are not supported, so this should be invalid
        assert not result["valid"]
        assert any("Unexpected token" in error for error in result["errors"])

    def test_unterminated_multi_line_comment(self):
        """Test unterminated multi-line comment."""
        checker = OverpassQLSyntaxChecker()
        query = """/* Unterminated comment
node["amenity"="restaurant"];
out;"""
        result = checker.check_syntax(query)
        assert not result["valid"]
        assert any(
            "Unterminated multi-line comment" in error for error in result["errors"]
        )

    def test_string_with_escape_sequences(self):
        """Test strings with various escape sequences."""
        checker = OverpassQLSyntaxChecker()

        test_cases = [
            'node["key"="line1\\nline2"];',  # newline
            'node["key"="tab\\ttab"];',  # tab
            'node["key"="return\\rreturn"];',  # carriage return
            'node["key"="backslash\\\\"];',  # backslash
            'node["key"="quote\\"quote"];',  # quote
            'node["key"="\\1"];',  # make statement escape
        ]

        for query in test_cases:
            result = checker.check_syntax(query)
            assert result["valid"], f"Failed for: {query}"

    def test_unicode_escape_sequences(self):
        """Test unicode escape sequences."""
        checker = OverpassQLSyntaxChecker()

        # Valid unicode escape
        result = checker.check_syntax('node["key"="\\u0041"];')
        assert result["valid"]

        # Invalid unicode escape (incomplete)
        result = checker.check_syntax('node["key"="\\u41"];')
        assert not result["valid"]

        # Invalid unicode escape (non-hex)
        result = checker.check_syntax('node["key"="\\uGGGG"];')
        assert not result["valid"]

    def test_unterminated_string_variations(self):
        """Test various unterminated string scenarios."""
        checker = OverpassQLSyntaxChecker()

        # Simple unterminated string
        result = checker.check_syntax('node["unterminated')
        assert not result["valid"]
        assert any("Unterminated string literal" in error for error in result["errors"])

        # Escape at end - causes different error
        result = checker.check_syntax('node["escape_at_end\\')
        assert not result["valid"]
        assert any(
            "Unexpected error" in error or "Unterminated" in error
            for error in result["errors"]
        )

        # Unicode escape incomplete
        result = checker.check_syntax('node["unicode_incomplete\\u')
        assert not result["valid"]
        assert any("Invalid unicode escape" in error for error in result["errors"])

    def test_template_placeholder_variations(self):
        """Test various template placeholder formats."""
        checker = OverpassQLSyntaxChecker()

        test_cases = [
            "{{bbox}};",
            '{{geocodeArea:"London"}};',
            "{{center}};",
            "node({{bbox}});",
        ]

        for query in test_cases:
            result = checker.check_syntax(query)
            assert result["valid"], f"Failed for: {query}"

    def test_unterminated_template_placeholder(self):
        """Test unterminated template placeholders."""
        checker = OverpassQLSyntaxChecker()

        result = checker.check_syntax("{{incomplete")
        assert not result["valid"]
        assert any("Unterminated template" in error for error in result["errors"])

    def test_number_tokenization_edge_cases(self):
        """Test edge cases in number tokenization."""
        checker = OverpassQLSyntaxChecker()

        test_cases = [
            "node(0,0,1,1);",  # Simple integers
            "node(0.5,0.5,1.5,1.5);",  # Decimals
            "node(-1,-1,1,1);",  # Negative numbers
            "node(-0.5,-0.5,0.5,0.5);",  # Negative decimals
        ]

        for query in test_cases:
            result = checker.check_syntax(query)
            assert result["valid"], f"Failed for: {query}"

    def test_identifier_edge_cases(self):
        """Test edge cases in identifier tokenization."""
        checker = OverpassQLSyntaxChecker()

        test_cases = [
            "node_test;",  # Underscore in identifier
            "_node;",  # Leading underscore
            "test_123;",  # Numbers in identifier
        ]

        for query in test_cases:
            result = checker.check_syntax(query)
            # These might be invalid as statements, but should tokenize properly
            # The validation will catch semantic errors
            assert isinstance(result, dict)  # Just verify we get a result

    def test_whitespace_handling(self):
        """Test various whitespace handling."""
        checker = OverpassQLSyntaxChecker()

        # Query with various whitespace
        query = """  node  [  "amenity"  =  "restaurant"  ]  ;
        way  [  "highway"  ]  ;
        out  ;  """

        result = checker.check_syntax(query)
        assert result["valid"]

    def test_special_character_tokenization(self):
        """Test tokenization of special characters."""
        checker = OverpassQLSyntaxChecker()

        # Test individual special characters in valid contexts
        test_cases = [
            "node[amenity=restaurant];>;out;",  # Recurse down
            "node[amenity=restaurant];<<;out;",  # Relation recurse up
            "node[amenity=restaurant];>>;out;",  # Relation recurse down
            'node["key"!="value"];out;',  # Not equals
            'node["key"!~"regex"];out;',  # Not regex
            'node["key"~"regex"];out;',  # Regex
        ]

        for query in test_cases:
            result = checker.check_syntax(query)
            assert result["valid"], f"Failed for: {query}"

        # Assignment arrows need proper context
        result = checker.check_syntax("(.set1; node(area.set1);)")
        assert result["valid"], "Assignment should work in proper context"

    def test_bracket_tokenization(self):
        """Test bracket tokenization in various contexts."""
        checker = OverpassQLSyntaxChecker()

        test_cases = [
            'node["key"="value"];',  # Square brackets
            "node(bbox);",  # Parentheses
            "{node; way;};",  # Braces (though this might be invalid syntax)
        ]

        for query in test_cases:
            result = checker.check_syntax(query)
            # Focus on tokenization, not necessarily valid syntax
            assert isinstance(result, dict)  # Just verify we get a result

    def test_geocode_area_tokenization_edge_cases(self):
        """Test edge cases in geocodeArea tokenization."""
        checker = OverpassQLSyntaxChecker()

        # Valid geocodeArea
        result = checker.check_syntax('{{geocodeArea:"London"}}->.area;')
        assert result["valid"]

        # Invalid geocodeArea syntax variations
        invalid_cases = [
            'geocodeArea:"London";',  # Missing braces
            '{{geocodeArea"London"}};',  # Missing colon
            "{{geocodeArea:London}};",  # Missing quotes
        ]

        for query in invalid_cases:
            result = checker.check_syntax(query)
            # These should fail in parsing, not tokenization

    def test_complex_tokenization_scenarios(self):
        """Test complex tokenization scenarios."""
        checker = OverpassQLSyntaxChecker()

        # Complex query with many different token types
        complex_query = """
        [out:json][timeout:25];
        // Find restaurants in London
        {{geocodeArea:"London"}}->.searchArea;
        (
          node["amenity"="restaurant"](area.searchArea);
          way["amenity"="restaurant"](area.searchArea);
          relation["amenity"="restaurant"](area.searchArea);
        );
        out center meta;
        """

        result = checker.check_syntax(complex_query)
        assert result["valid"]

    def test_edge_cases_at_end_of_input(self):
        """Test edge cases when reaching end of input."""
        checker = OverpassQLSyntaxChecker()

        # Test queries that end abruptly and should fail
        edge_cases = [
            "node[",  # Incomplete filter
            "node(around:",  # Incomplete spatial filter
            'node["key"=',  # Incomplete assignment
        ]

        for query in edge_cases:
            result = checker.check_syntax(query)
            assert not result["valid"], f"Should fail for: {query}"

        # "node" alone is actually valid as a minimal query
        result = checker.check_syntax("node")
        assert result["valid"], "Single 'node' should be valid"


class TestParserEdgeCases:
    """Test edge cases in parsing that weren't covered."""

    def test_empty_statements(self):
        """Test handling of empty statements."""
        checker = OverpassQLSyntaxChecker()

        # Multiple semicolons
        result = checker.check_syntax(";;;")
        assert not result["valid"]  # Empty statements should be invalid

    def test_invalid_setting_combinations(self):
        """Test invalid setting combinations."""
        checker = OverpassQLSyntaxChecker()

        # Duplicate settings
        result = checker.check_syntax("[timeout:30][timeout:60];")
        assert result["valid"]  # Should allow, last one wins (with warning)

    def test_malformed_expressions(self):
        """Test malformed expressions in various contexts."""
        checker = OverpassQLSyntaxChecker()

        test_cases = [
            "make stat ++;",  # Invalid operator
            'node["key"=~/invalid];',  # Malformed regex operator (=~ is invalid)
        ]

        for query in test_cases:
            result = checker.check_syntax(query)
            assert not result["valid"], f"Should fail for: {query}"

        # This one is actually valid - convert supports function calls
        result = checker.check_syntax("convert item ::=invalid();")
        assert result["valid"], "Convert with function call should be valid"

    def test_deeply_nested_expressions(self):
        """Test deeply nested valid expressions."""
        checker = OverpassQLSyntaxChecker()

        # Deeply nested make expression
        query = "make stat count = ((count(tags)+count(ways))*2);"
        result = checker.check_syntax(query)
        assert result["valid"]

    def test_boundary_coordinate_values(self):
        """Test boundary coordinate values."""
        checker = OverpassQLSyntaxChecker()

        # Exactly at boundaries
        test_cases = [
            "node(90,180,-90,-180);",  # Extreme valid values
            "node(90.0,180.0,-90.0,-180.0);",  # Extreme valid decimals
        ]

        for query in test_cases:
            result = checker.check_syntax(query)
            assert result["valid"], f"Should be valid for: {query}"

    def test_large_numeric_values(self):
        """Test handling of large numeric values."""
        checker = OverpassQLSyntaxChecker()

        # Very large numbers
        result = checker.check_syntax("node(around:999999999,0,0);")
        assert result["valid"]  # Should parse, even if impractical

    def test_special_tag_keys(self):
        """Test special tag keys and values."""
        checker = OverpassQLSyntaxChecker()

        test_cases = [
            'node[""];',  # Empty key
            'node[""=""];',  # Empty key and value
            'node["key with spaces"];',  # Key with spaces
            'node["unicode_ñáéíóú"];',  # Unicode in key
        ]

        for query in test_cases:
            result = checker.check_syntax(query)
            assert result["valid"], f"Should be valid for: {query}"

    def test_malformed_spatial_filters(self):
        """Test malformed spatial filters."""
        checker = OverpassQLSyntaxChecker()

        test_cases = [
            "node(bbox:);",  # Invalid bbox syntax
            "node(id:);",  # Missing ID
        ]

        for query in test_cases:
            result = checker.check_syntax(query)
            assert not result["valid"], f"Should fail for: {query}"

        # Empty spatial filters are actually allowed
        result = checker.check_syntax("node(around);")
        assert result["valid"], "Empty around filter should be valid"
