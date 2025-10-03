#!/usr/bin/env python3
"""
Script to find any remaining invalid queries in the test suite.
"""

import os
import sys

from overpass_ql_checker import OverpassQLSyntaxChecker

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_complex_edge_cases():
    """Test various edge cases that might still be invalid."""

    checker = OverpassQLSyntaxChecker()

    # Some potentially problematic queries
    test_queries = [
        # Malformed syntax
        "node[",
        "node[]",
        "[out:json",
        "node[amenity=",
        'node[amenity="',
        'node[amenity="restaurant]',
        # Incomplete constructs
        "for(",
        "for()",
        "for(user(",
        "if(",
        "if(t[",
        # Bad coordinates
        "node(around:abc,1.0,2.0)",
        "node(around:1.0,abc,2.0)",
        "node(50.0,10.0,50.0)",  # incomplete bbox
        # Bad numbers/dates
        'node(changed:"invalid-date")',
        'node(changed:"2020-13-40")',
        "[timeout:abc]",
        # Malformed regex
        'node[name~"["]',
        'node[name~"[a-z"]',  # unclosed bracket
        # Bad output formats
        "[out:invalid_format]",
        "[out:pbf]",  # might not be supported
        # Unclosed structures
        "(node[amenity=restaurant",
        "node[amenity=restaurant];(",
        ".a; .b;)",
        # Invalid identifiers
        "node[123invalid=value]",
        "123invalid[amenity=restaurant]",
        # Bad assignments
        "->.123",
        "->.",
        "node->.123invalid",
        # Malformed templates
        "{{}}",
        "{{invalid",
        "{{bbox=}}",
        # Invalid filters
        "node(if:)",
        "node(around:)",
        "node(id:)",
        "node(uid:abc)",
        # Bad set operations
        "(; .a)",
        "(.a; )",
        "- .a",
        # Unicode/encoding issues
        'node[name="café\x00"]',  # null byte
        'node[name="\x01\x02"]',  # control chars
        # Very long strings (might cause issues)
        f'node[name="{"a" * 10000}"]',
        # Nested quotes
        'node[name=""test""]',
        "node[name='test']",  # single quotes not supported
        # Bad spatial filters
        'node(newer:"invalid")',
        "node(user:)",
        "node(uid:)",
    ]

    invalid_count = 0
    invalid_queries = []

    print("Testing potentially problematic queries...")
    print("=" * 60)

    for i, query in enumerate(test_queries, 1):
        try:
            result = checker.check_syntax(query)
            if not result.is_valid:
                invalid_count += 1
                invalid_queries.append((query, result.errors))
                print(f"❌ Query {i}: {query[:50]}{'...' if len(query) > 50 else ''}")
                for error in result.errors:
                    print(f"   Error: {error}")
                print()
        except Exception as e:
            invalid_count += 1
            invalid_queries.append((query, [f"Exception: {e}"]))
            query_preview = f"{query[:50]}{'...' if len(query) > 50 else ''}"
            print(f"💥 Query {i} (Exception): {query_preview}")
            print(f"   Exception: {e}")
            print()

    print("=" * 60)
    print(f"Found {invalid_count} invalid queries out of {len(test_queries)} tested")

    if invalid_count > 0:
        print("\nInvalid queries summary:")
        for query, errors in invalid_queries:
            print(f"- {query}")
            for error in errors:
                print(f"  → {error}")

    return invalid_queries


if __name__ == "__main__":
    invalid_queries = test_complex_edge_cases()

    if invalid_queries:
        print(f"\n🔍 Found {len(invalid_queries)} queries that need fixing!")
    else:
        print("\n✅ All test queries are now valid!")
