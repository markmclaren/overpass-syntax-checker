#!/usr/bin/env python3

import os
import sys

from overpass_ql_checker.checker import OverpassQLSyntaxChecker

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


def test_more_queries():
    """Test more sample queries from the invalid_queries.txt file."""

    # Read more sample queries including some that should be easier to fix
    sample_queries = [
        # Query with simple around filter
        (
            '(node["amenity"="bar"](around:1000,48.195085,16.3515152);'
            'node["amenity"="pub"](around:1000,48.195085,16.3515152);'
            'node["amenity"="restaurant"](around:1000,48.195085,16.3515152);)->.me;'
            '(node["amenity"="bar"](around:1000,48.2024352,16.3378693);'
            'node["amenity"="pub"](around:1000,48.2024352,16.3378693);'
            'node["amenity"="restaurant"](around:1000,48.2024352,16.3378693);)'
            "->.julian;node.me.julian;out;"
        ),
        # Query with area filter
        (
            "[out:xml][timeout:120];area(3600061549)->.area;"
            '(way["name"~"Pourvoirie"](area.area);'
            'node["name"~"Pourvoirie"](area.area););out meta;>;out meta;'
        ),
        # Query with simple around parameterless
        (
            '[timeout:600];{{geocodeArea:"MA"}}->.searchArea;'
            '(way["amenity"="pharmacy"](area.searchArea);'
            'node["amenity"="pharmacy"](area.searchArea););'
            'way["amenity"="parking"](around:200);(._;>;);out;'
        ),
        # Query with minus operation
        (
            'relation["route"="hiking"]({{bbox}})->.h;'
            'relation["route"="mtb"]({{bbox}})->.b;'
            '(way["bicycle"="designated"]["highway"="path"](r.h);'
            '-way["bicycle"="designated"]["highway"="path"](r.b););'
            'out meta geom;relation["route"="hiking"](bw);out meta; '
            "{{bbox=area:3606195356}}"
        ),
        # Query with simple node lookup
        (
            'node[name="Oberlar"]->.zentrum;'
            "node(around.zentrum:200.0)[highway=bus_stop]->.a;.a out;"
            "node(around.zentrum:500.0)[highway=bus_stop]->.b;"
            "(.b; - .a;)->.diff;.diff out;"
            "node(around.zentrum:1000.0)[highway=bus_stop]->.c;"
            "(.c; - .b;)->.diff;.diff out;"
        ),
    ]

    checker = OverpassQLSyntaxChecker()

    total_queries = len(sample_queries)
    valid_queries = 0

    for i, query in enumerate(sample_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Testing Query {i}:")
        print(f"{'=' * 60}")
        print(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
        print()

        result = checker.check_syntax(query)

        print(f"Valid: {result['valid']}")
        if result["valid"]:
            valid_queries += 1

        if result["errors"]:
            print("\nErrors:")
            for error in result["errors"][:3]:  # Limit to first 3 errors
                print(f"  - {error}")
            if len(result["errors"]) > 3:
                print(f"  ... and {len(result['errors']) - 3} more errors")

        if result["warnings"]:
            print("\nWarnings:")
            for warning in result["warnings"][:2]:  # Limit to first 2 warnings
                print(f"  - {warning}")

    print(f"\n{'=' * 60}")
    print(
        f"SUMMARY: {valid_queries}/{total_queries} queries are now valid "
        f"({100 * valid_queries / total_queries:.1f}%)"
    )
    print(f"{'=' * 60}")


if __name__ == "__main__":
    test_more_queries()
