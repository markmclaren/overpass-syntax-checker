#!/usr/bin/env python3

import os
import sys

from overpass_ql_checker.checker import OverpassQLSyntaxChecker

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


def test_sample_queries():
    """Test some sample queries from the invalid_queries.txt file."""

    # Read a few sample queries
    sample_queries = [
        # First query from the file
        (
            "area(3600062484)->.s;"
            '(node["addr:housenumber"="8"]["addr:street"="Ellermühle"](area.s);'
            'way["addr:housenumber"="8"]["addr:street"="Ellermühle"](area.s);'
            'relation["addr:housenumber"="8"]["addr:street"="Ellermühle"](area.s);'
            ");out;>;out skel qt;"
        ),
        # Second query
        (
            'relation["route"="hiking"]({{bbox}})->.h;'
            'relation["route"="mtb"]({{bbox}})->.b;'
            '(way["bicycle"="designated"]["highway"="path"](r.h);'
            '-way["bicycle"="designated"]["highway"="path"](r.b););'
            'out meta geom;relation["route"="hiking"](bw);out meta; '
            "{{bbox=area:3606195356}}"
        ),
        # A simpler one
        (
            "[out:csv(user,total,nodes,ways,relations)][timeout:25];"
            '( nwr["amenity"="place_of_worship"]({{bbox}}); '
            'nwr["shop"="convenience"]({{bbox}}););'
            'for (user()){ make stat "user"=_.val, nodes=count(nodes), '
            "ways=count(ways), relations=count(relations), "
            "total = count(nodes) + count(ways) + count(relations); out;};"
        ),
        # One with template placeholders
        (
            '{{geocodeArea:"MA"}}->.searchArea;'
            '(way["amenity"="pharmacy"](area.searchArea);'
            'node["amenity"="pharmacy"](area.searchArea););'
            'way["amenity"="parking"](around:200);(._;>;);out;'
        ),
    ]

    checker = OverpassQLSyntaxChecker()

    for i, query in enumerate(sample_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Testing Query {i}:")
        print(f"{'=' * 60}")
        print(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
        print()

        result = checker.check_syntax(query)

        print(f"Valid: {result['valid']}")

        if result["errors"]:
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")

        if result["warnings"]:
            print("\nWarnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")


if __name__ == "__main__":
    test_sample_queries()
