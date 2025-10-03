#!/usr/bin/env python3

import os
import sys

# Add the src directory to Python path to import the checker
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from overpass_ql_checker.checker import OverpassQLSyntaxChecker

def analyze_invalid_queries():
    """Analyze the invalid queries from invalid_queries_comments.txt"""
    
    # Read the queries from the file
    queries_file = os.path.join(os.path.dirname(__file__), '..', 'invalid_queries_comments.txt')
    
    with open(queries_file, 'r', encoding='utf-8') as f:
        queries = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(queries)} queries to analyze\n")
    
    checker = OverpassQLSyntaxChecker()
    
    valid_count = 0
    invalid_count = 0
    error_patterns = {}
    
    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query[:80]}{'...' if len(query) > 80 else ''}")
        
        try:
            result = checker.check_syntax(query)
            is_valid = result['valid']
            if is_valid:
                print("  ✓ Current checker considers this VALID")
                valid_count += 1
            else:
                print("  ✗ Current checker considers this INVALID")
                invalid_count += 1
                
                # Get detailed error info
                errors = result.get('errors', [])
                if errors:
                    for error in errors[:2]:  # Show first 2 errors
                        print(f"    Error: {error}")
                        
                        # Categorize error patterns by type of error message
                        if "Expected" in error:
                            error_type = "Expected Token"
                        elif "Unexpected" in error:
                            error_type = "Unexpected Token"
                        elif "Invalid" in error:
                            error_type = "Invalid Syntax"
                        elif "Unknown" in error:
                            error_type = "Unknown Element"
                        else:
                            error_type = "Other Error"
                            
                        if error_type not in error_patterns:
                            error_patterns[error_type] = 0
                        error_patterns[error_type] += 1
                    
        except Exception as e:
            print(f"  ! Exception during validation: {e}")
            invalid_count += 1
            
        print()
    
    print("\n=== Summary ===")
    print(f"Total queries: {len(queries)}")
    print(f"Currently detected as valid: {valid_count}")
    print(f"Currently detected as invalid: {invalid_count}")
    
    if error_patterns:
        print("\nError pattern distribution:")
        for pattern, count in sorted(error_patterns.items()):
            print(f"  {pattern}: {count}")

if __name__ == "__main__":
    analyze_invalid_queries()