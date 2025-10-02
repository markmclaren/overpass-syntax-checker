#!/usr/bin/env python3
"""
Test script to debug template placeholder handling
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from overpass_ql_checker import OverpassQLSyntaxChecker

def test_template_handling():
    """Test template placeholder handling."""
    
    checker = OverpassQLSyntaxChecker()
    
    test_queries = [
        # Simple template
        'node[amenity=restaurant]({{bbox}});out;',
        
        # GeocodeArea template
        '{{geocodeArea:"Kyiv"}}->.searchArea;node(area.searchArea);out;',
        
        # Multiple templates
        'relation["route"="hiking"]({{bbox}})->.h;',
        
        # The first problematic query from the file
        'relation["route"="hiking"]({{bbox}})->.h;relation["route"="mtb"]({{bbox}})->.b;(way["bicycle"="designated"]["highway"="path"](r.h);-way["bicycle"="designated"]["highway"="path"](r.b););out meta geom;relation["route"="hiking"](bw);out meta; {{bbox=area:3606195356}}'
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
        tokens = result.get('tokens', [])
        print(f"Tokens ({len(tokens)}): {', '.join(tokens[:10])}")
        if len(tokens) > 10:
            print(f"  ... and {len(tokens) - 10} more")

if __name__ == "__main__":
    test_template_handling()