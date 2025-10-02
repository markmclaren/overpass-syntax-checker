#!/usr/bin/env python3
"""Test script to check why some queries are being flagged as invalid."""

import os
import sys

from overpass_ql_checker.checker import OverpassQLSyntaxChecker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def check_query(query, description=""):
    """Test a single query and print results."""
    print(f"\n=== Testing Query: {description} ===")
    print(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")

    checker = OverpassQLSyntaxChecker()
    result = checker.check_syntax(query)

    print(f"Valid: {result['valid']}")
    if result["errors"]:
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")
    if result["warnings"]:
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")


def main():
    """Test several sample queries from the invalid_queries.txt file."""

    # Sample queries from the file
    sample_queries = [
        # Simple query with bbox template
        (
            (
                'relation["route"="hiking"]({{bbox}})->.h;'
                'relation["route"="mtb"]({{bbox}})->.b;'
                '(way["bicycle"="designated"]["highway"="path"](r.h);'
                '-way["bicycle"="designated"]["highway"="path"](r.b););'
                'out meta geom;relation["route"="hiking"](bw);out meta; '
                "{{bbox=area:3606195356}}"
            ),
            "Query with bbox template",
        ),
        # Query with CSV output
        (
            (
                "[out:csv(user,total,nodes,ways,relations)][timeout:25];"
                '( nwr["amenity"="place_of_worship"]({{bbox}}); '
                'nwr["shop"="convenience"]({{bbox}}););'
                'for (user()){ make stat "user"=_.val, nodes=count(nodes), '
                "ways=count(ways), relations=count(relations), "
                "total = count(nodes) + count(ways) + count(relations); out;};"
            ),
            "CSV output query",
        ),
        # Simple area query
        (
            (
                'area["admin_level"="8"]["name"="Alfortville"]->.a;'
                'nwr["amenity"="bicycle_parking"](area.a);'
                'nwr._(if:is_number(t["capacity"]));'
                'make total num=sum(t["capacity"]);out;'
            ),
            "Area query with make statement",
        ),
        # Query with geocodeArea
        (
            (
                '[out:json][timeout:100];{{geocodeArea:"Bernareggio"}}->.area;'
                'node["addr:housenumber"](area)->.hnum_sep;'
                'way["addr:housenumber"](area)->.hnum_in;'
                '(way["building"](around.hnum_sep:20);'
                'way["building"](around.hnum_in:20););out;out;>;out skel qt;'
            ),
            "geocodeArea query",
        ),
        # Simple template query
        (
            (
                'node[name="Oberlar"]->.zentrum;'
                "node(around.zentrum:200.0)[highway=bus_stop]->.a;.a out;"
            ),
            "Simple template query",
        ),
    ]

    for query, description in sample_queries:
        check_query(query, description)


if __name__ == "__main__":
    main()
