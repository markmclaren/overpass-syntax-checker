#!/usr/bin/env python3

import os
import sys

# Add the src directory to Python path to import the checker
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from overpass_ql_checker.checker import OverpassQLSyntaxChecker


def test_invalid_output_formats():
    """Test that invalid output formats are properly rejected"""
    checker = OverpassQLSyntaxChecker()
    
    invalid_formats = [
        '[out:osm];node[name="test"];out;',
        '[out:xlsx];node[name="test"];out;', 
        '[out:pjsonl];way[highway];out;',
        '[timeout:25][out:osm];node["place"];out;',
    ]
    
    print("Testing invalid output formats...")
    for i, query in enumerate(invalid_formats, 1):
        result = checker.check_syntax(query)
        assert not result['valid'], f"Query {i} should be invalid: {query}"
        assert any("Invalid output format" in error for error in result['errors']), \
            f"Query {i} should have output format error"
        print(f"  ✓ Query {i}: Correctly rejected invalid output format")


def test_invalid_date_formats():
    """Test that invalid date formats with timezone suffixes are rejected"""
    checker = OverpassQLSyntaxChecker()
    
    invalid_dates = [
        '[date:"2014-05-13T00:00:00H"];node["building"];out;',
        '[date:"2020-03-01T00:00:00+09:00"];node["amenity"];out;',
        '[date:"2020-04-01T00:00:00+09:00"];way["highway"];out;',
        '[date:"2020-05-01T00:00:00+09:00"];relation["type"];out;',
    ]
    
    print("Testing invalid date formats...")
    for i, query in enumerate(invalid_dates, 1):
        result = checker.check_syntax(query)
        assert not result['valid'], f"Query {i} should be invalid: {query}"
        assert any("Invalid date format" in error for error in result['errors']), \
            f"Query {i} should have date format error"
        print(f"  ✓ Query {i}: Correctly rejected invalid date format")


def test_complex_arrow_operator_issues():
    """Test complex arrow operator syntax issues"""
    checker = OverpassQLSyntaxChecker()
    
    arrow_issues = [
        'relation["route"~"^hiking$"]({{bbox}});>->.r;((way["colour"]({{bbox}});-way.r;);>->.x;<;);out;',
        'way["waterway"="stream"]({{bbox}})->.CurrentWaterWay;node(w.CurrentWaterWay)->.NodesOfCurrentWaterWay;.NodesOfCurrentWaterWay out;for.NodesOfCurrentWaterWay->.z(id()){make debug Nodes=z.val;out;if(..count_members==..count_members){}.z->.lastNode;}make debug enters="------------";out;.lastNode out;',
        '((way["highway"]["colour"]["area"!~"."](area:3601473946);way(165060349););(._;>->.x;<;);out;',
    ]
    
    print("Testing complex arrow operator issues...")
    for i, query in enumerate(arrow_issues, 1):
        result = checker.check_syntax(query)
        assert not result['valid'], f"Query {i} should be invalid: {query}"
        # These should have syntax errors related to arrow operators or unexpected tokens
        has_arrow_error = any("Unexpected token: ->" in error or "Expected ), got ." in error 
                             for error in result['errors'])
        assert has_arrow_error, f"Query {i} should have arrow operator error"
        print(f"  ✓ Query {i}: Correctly rejected complex arrow syntax")


def test_foreach_and_set_issues():
    """Test foreach loop and set name parsing issues"""
    checker = OverpassQLSyntaxChecker()
    
    set_issues = [
        'relation(416351);foreach->.rel{way["wikidata"](r.rel)->.ways;relation.rel;out;}',
        'way["wikidata"]({{bbox}});foreach->.rel{way.all(r.rel)->.ways;relation.rel;out;}',
        'area[name="test"];relation["boundary"](area);map_to_area;foreach->.rel{relation.rel;out;}',
    ]
    
    print("Testing foreach and set name issues...")
    for i, query in enumerate(set_issues, 1):
        result = checker.check_syntax(query)
        assert not result['valid'], f"Query {i} should be invalid: {query}"
        # These should have syntax errors related to set names
        has_set_error = any("Expected set name after" in error or "Expected ;, got" in error 
                           for error in result['errors'])
        assert has_set_error, f"Query {i} should have set name error"
        print(f"  ✓ Query {i}: Correctly rejected set name syntax")


def test_area_parameter_issues():
    """Test area parameter and geocode syntax issues"""
    checker = OverpassQLSyntaxChecker()
    
    area_issues = [
        '[date:"2014-05-13T00:00:00H"];{{geocodeArea:"El Segundo"}}->.searchArea;(node["building"](area.searchArea);way["building"](area.searchArea);relation["building"](area.searchArea););out qt geom;',
        '[out:json][timeout:25];{{geocodeArea:"Duisburg"}}->.searchArea;(node["memorial:type"="stolperstein"](area.searchArea);area(area.searchArea););out;>;out skel qt;',
    ]
    
    print("Testing area parameter issues...")
    for i, query in enumerate(area_issues, 1):
        result = checker.check_syntax(query)
        assert not result['valid'], f"Query {i} should be invalid: {query}"
        print(f"  ✓ Query {i}: Correctly rejected area syntax issue")


def test_convert_statement_issues():
    """Test convert statement syntax issues"""
    checker = OverpassQLSyntaxChecker()
    
    convert_issues = [
        '[out:json][timeout:1000];node["public_transport"="stop_position"]["name"]["bus"="yes"](around:100,45.1933211,5.7326121)->.bus_stop;foreach.bus_stop->.stop{(node.bus_stop;<;)->.bus_way_rel;relation.bus_way_rel["route"="bus"]["ref"]->.bus_rel;convert bus_stop_info ::=id(),!lines;out;}(node.bus_stop;<;)->.bus_way_rel;relation.bus_way_rel["route"="bus"]["ref"]->.bus_rel;.bus_rel out count;.bus_rel out;.bus_stop out count;.bus_stop out;',
    ]
    
    print("Testing convert statement issues...")
    for i, query in enumerate(convert_issues, 1):
        result = checker.check_syntax(query)
        assert not result['valid'], f"Query {i} should be invalid: {query}"
        print(f"  ✓ Query {i}: Correctly rejected convert statement syntax")


def test_all_invalid_query_samples():
    """Test all 30 invalid queries from the file to ensure they're caught"""
    checker = OverpassQLSyntaxChecker()
    
    # Read the queries from the file
    queries_file = os.path.join(os.path.dirname(__file__), '..', 'invalid_queries_comments.txt')
    
    with open(queries_file, 'r', encoding='utf-8') as f:
        queries = [line.strip() for line in f if line.strip()]
    
    print(f"Testing all {len(queries)} invalid queries from file...")
    
    for i, query in enumerate(queries, 1):
        result = checker.check_syntax(query)
        assert not result['valid'], f"Query {i} should be invalid: {query[:50]}..."
        assert len(result['errors']) > 0, f"Query {i} should have error messages"
        
    print(f"  ✓ All {len(queries)} queries correctly identified as invalid")


def run_comprehensive_invalid_tests():
    """Run all invalid query tests"""
    print("="*60)
    print("COMPREHENSIVE INVALID QUERY TESTS")
    print("="*60)
    
    test_invalid_output_formats()
    print()
    
    test_invalid_date_formats()
    print()
    
    test_complex_arrow_operator_issues()
    print()
    
    test_foreach_and_set_issues()
    print()
    
    test_area_parameter_issues()
    print()
    
    test_convert_statement_issues()
    print()
    
    test_all_invalid_query_samples()
    print()
    
    print("="*60)
    print("✅ ALL TESTS PASSED!")
    print("The checker correctly identifies all invalid query patterns.")
    print("="*60)


if __name__ == "__main__":
    run_comprehensive_invalid_tests()