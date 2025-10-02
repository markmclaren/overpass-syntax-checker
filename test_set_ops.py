#!/usr/bin/env python3
"""
Test script to debug set operations and references
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from overpass_ql_checker import OverpassQLSyntaxChecker

def test_set_operations():
    """Test set operations and references."""
    
    checker = OverpassQLSyntaxChecker()
    
    test_queries = [
        # Simple set reference (should work)
        '.mySet out;',
        
        # Set operations (might be problematic)
        '(._;>;);out;',
        '(._;->.b;);out;',
        
        # From the invalid queries file
        'node[name="Oberlar"]->.zentrum;node(around.zentrum:200.0)[highway=bus_stop]->.a;.a out;node(around.zentrum:500.0)[highway=bus_stop]->.b;(.b; - .a;)->.diff;.diff out;',
        
        # Another complex one
        '[bbox:{{bbox}}];way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|(motorway|trunk|primary|secondary)_link)$"]->.major;way["highway"~"^(unclassified|residential|living_street|service)$"]->.minor;node["area"!~".*"](w.major)(w.minor)({{bbox}});(way["building"~"."](around:0);node(w););out;'
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n--- Test {i+1} ---")
        print(f"Query: {query[:80]}{'...' if len(query) > 80 else ''}")
        
        result = checker.check_syntax(query)
        
        if result['valid']:
            print("✅ VALID")
        else:
            print("❌ INVALID")
            for error in result['errors'][:3]:  # First 3 errors
                print(f"  Error: {error}")
        
        # Show tokens for debugging
        if not result['valid']:
            tokens = result.get('tokens', [])
            print(f"Tokens ({len(tokens)}): {', '.join(tokens[:15])}")
            if len(tokens) > 15:
                print(f"  ... and {len(tokens) - 15} more")

if __name__ == "__main__":
    test_set_operations()