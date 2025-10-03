#!/usr/bin/env python3

import os
import sys

# Add the src directory to Python path to import the checker
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from overpass_ql_checker.checker import OverpassQLSyntaxChecker

def categorize_invalid_query_errors():
    """Categorize the specific types of errors in the invalid queries"""
    
    # Read the queries from the file
    queries_file = os.path.join(os.path.dirname(__file__), '..', 'invalid_queries_comments.txt')
    
    with open(queries_file, 'r', encoding='utf-8') as f:
        queries = [line.strip() for line in f if line.strip()]
    
    print(f"Analyzing error patterns in {len(queries)} invalid queries\n")
    
    checker = OverpassQLSyntaxChecker()
    
    # Categories of errors we'll track
    error_categories = {
        'arrow_operator': [],  # Issues with -> operator
        'output_format': [],   # Invalid output formats
        'date_format': [],     # Date format issues  
        'set_names': [],       # Set name parsing issues
        'foreach_loops': [],   # Issues with foreach syntax
        'area_parameters': [], # Area parameter issues
        'convert_statement': [], # Issues with convert statements
        'other': []           # Other unclassified errors
    }
    
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}:")
        print(f"  {query[:100]}{'...' if len(query) > 100 else ''}")
        
        result = checker.check_syntax(query)
        errors = result.get('errors', [])
        
        for error in errors[:1]:  # Look at first error for categorization
            error_lower = error.lower()
            
            if 'unexpected token: ->' in error_lower or 'expected ), got .' in error_lower:
                error_categories['arrow_operator'].append((i, query, error))
                print(f"  → ARROW OPERATOR: {error}")
            elif 'invalid output format' in error_lower:
                error_categories['output_format'].append((i, query, error))
                print(f"  → OUTPUT FORMAT: {error}")
            elif 'invalid date format' in error_lower:
                error_categories['date_format'].append((i, query, error))
                print(f"  → DATE FORMAT: {error}")
            elif 'expected set name after' in error_lower:
                error_categories['set_names'].append((i, query, error))
                print(f"  → SET NAMES: {error}")
            elif 'foreach' in error_lower:
                error_categories['foreach_loops'].append((i, query, error))
                print(f"  → FOREACH: {error}")
            elif 'expected area parameter' in error_lower:
                error_categories['area_parameters'].append((i, query, error))
                print(f"  → AREA PARAM: {error}")
            elif 'convert' in error_lower:
                error_categories['convert_statement'].append((i, query, error))
                print(f"  → CONVERT: {error}")
            else:
                error_categories['other'].append((i, query, error))
                print(f"  → OTHER: {error}")
    
    print("\n" + "="*60)
    print("ERROR CATEGORY SUMMARY")
    print("="*60)
    
    for category, errors in error_categories.items():
        if errors:
            print(f"\n{category.upper().replace('_', ' ')} ({len(errors)} queries):")
            for query_num, query, error in errors:
                print(f"  Query {query_num}: {error}")
    
    # Analysis of what might need fixing
    print("\n" + "="*60)
    print("POTENTIAL IMPROVEMENTS NEEDED")
    print("="*60)
    
    if error_categories['arrow_operator']:
        print(f"\n• Arrow operator parsing ({len(error_categories['arrow_operator'])} cases)")
        print("  Many queries use complex arrow syntax that might be valid in real Overpass QL")
        
    if error_categories['output_format']:
        print(f"\n• Output format support ({len(error_categories['output_format'])} cases)")
        print("  Missing support for: osm, xlsx, pjsonl formats")
        
    if error_categories['date_format']:
        print(f"\n• Date format parsing ({len(error_categories['date_format'])} cases)")
        print("  Missing support for timezone suffixes like +09:00")
        
    if error_categories['set_names']:
        print(f"\n• Set name handling ({len(error_categories['set_names'])} cases)")
        print("  Issues with foreach loops and set operations")
        
    if error_categories['area_parameters']:
        print(f"\n• Area parameter parsing ({len(error_categories['area_parameters'])} cases)")
        print("  Issues with complex area expressions")

if __name__ == "__main__":
    categorize_invalid_query_errors()