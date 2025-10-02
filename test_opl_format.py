#!/usr/bin/env python3
"""
Test script to debug opl output format
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from overpass_ql_checker import OverpassQLSyntaxChecker

def test_opl_format():
    """Test opl output format."""
    
    checker = OverpassQLSyntaxChecker()
    
    test_queries = [
        # Standard formats (should work)
        '[out:json];node[amenity=restaurant];out;',
        '[out:xml];node[amenity=restaurant];out;',
        '[out:csv("name")];node[amenity=restaurant];out;',
        
        # OPL format (was failing)
        '[out:opl];node[amenity=restaurant];out;',
        
        # The actual problematic query from the file
        '[out:opl];(node["xmas:feature"];way["xmas:feature"];relation["xmas:feature"];);(._;>;);out meta;'
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

if __name__ == "__main__":
    test_opl_format()