#!/usr/bin/env python3
"""
Test the Overpass QL Syntax Checker with complex real-world queries.
"""

from overpass_ql_checker import OverpassQLSyntaxChecker


def test_complex_queries():
    """Test complex real-world Overpass QL queries."""
    checker = OverpassQLSyntaxChecker()

    # Complex real-world queries
    queries = [
        # 1. Restaurant query with area and union
        {
            "name": "Berlin Restaurants",
            "query": """
            [out:json][timeout:25];
            area[name="Berlin"]->.searchArea;
            (
              node(area.searchArea)[amenity=restaurant];
              way(area.searchArea)[amenity=restaurant];
              relation(area.searchArea)[amenity=restaurant];
            );
            out center;
            """,
            "should_pass": True,
        },
        # 2. Public transport query with multiple filters
        {
            "name": "Public Transport in Bounding Box",
            "query": """
            [out:json][bbox:52.5,13.3,52.6,13.5];
            (
              node[public_transport=stop_position];
              node[highway=bus_stop];
              way[highway=bus_guideway];
              rel[type=route][route~"^(bus|tram|subway)$"];
            );
            out geom;
            """,
            "should_pass": True,
        },
        # 3. Around query with recursion
        {
            "name": "Amenities Around Point with Recursion",
            "query": """
            [out:json];
            (
              node(around:1000,52.5200,13.4050)[amenity~"^(restaurant|cafe|bar)$"];
              way(around:1000,52.5200,13.4050)[amenity~"^(restaurant|cafe|bar)$"];
            );
            (._;>;);
            out;
            """,
            "should_pass": True,
        },
        # 4. Historical data query
        {
            "name": "Historical OSM Data",
            "query": """
            [out:json][date:"2020-01-01T00:00:00Z"];
            node[amenity=restaurant](50.0,7.0,51.0,8.0);
            out meta;
            """,
            "should_pass": True,
        },
        # 5. Complex regex and tag filters
        {
            "name": "Complex Tag Filtering",
            "query": """
            [out:json];
            node[~"^addr:.*$"~".*"][name~"Hotel.*", i][tourism=hotel];
            out;
            """,
            "should_pass": True,
        },
        # 6. Foreach loop example
        {
            "name": "Foreach Loop",
            "query": """
            [out:json];
            way[highway=primary];
            foreach {
              (._; >;);
              out;
            }
            """,
            "should_pass": True,
        },
        # 7. CSV output with custom fields
        {
            "name": "CSV Output",
            "query": """
            [out:csv(::id, ::type, name, amenity, "addr:street"; false; "|")];
            node[amenity=restaurant](50.0,7.0,51.0,8.0);
            out;
            """,
            "should_pass": True,
        },
        # 8. Error: Missing semicolon
        {
            "name": "Missing Semicolon",
            "query": """
            [out:json]
            node[amenity=restaurant]
            out;
            """,
            "should_pass": False,
        },
        # 9. Error: Invalid regex
        {
            "name": "Invalid Regex",
            "query": """
            [out:json];
            node[name~"[invalid"];
            out;
            """,
            "should_pass": False,
        },
        # 10. Error: Invalid coordinates
        {
            "name": "Invalid Coordinates",
            "query": """
            [out:json];
            node(200.0,-200.0,91.0,181.0);
            out;
            """,
            "should_pass": False,
        },
        # 11. Real-world: Geocoding with area search
        {
            "name": "Geocoding Area Search",
            "query": """
            [out:json][timeout:25];
            {{geocodeArea:"Deutschland"}}->.searchArea;
            node["historic"="castle"](area.searchArea);
            out;
            """,
            "should_pass": True,
        },
        # 12. Real-world: Complex relation query with recursion
        {
            "name": "Complex Relation with Recursion",
            "query": """
            [out:json][timeout:25];
            {{geocodeArea:"Magnitogorsk"}}->.searchArea;
            way["railway"="tram"]["service"="yard"]["service"="spur"]["service"="siding"]["service"="crossover"](area.searchArea);
            out;
            """,
            "should_pass": True,
        },
        # 13. Real-world: Administrative boundaries
        {
            "name": "Administrative Boundaries",
            "query": """
            [out:json][timeout:25];
            {{geocodeArea:"gridan"}}->.searchArea;
            relation["admin_level"="10"]["boundary"="administrative"](area.searchArea);
            out;
            """,
            "should_pass": True,
        },
        # 14. Real-world: CSV output with custom fields
        {
            "name": "CSV Output with Custom Fields",
            "query": """
            [out:csv("name","amenity","addr:city","addr:street","addr:housenumber";false;"|")];
            area["de:amtlicher_gemeindeschluessel"~"^051"];
            out;
            """,
            "should_pass": True,
        },
        # 15. Real-world: Historical data with date
        {
            "name": "Historical Data Query",
            "query": """
            [out:xml][timeout:30];
            way(uid:7725447)[changed:"2019-02-11T00:00:00Z","2019-02-11T23:55:59Z"];
            node(uid:7725447)[changed:"2019-02-11T00:00:00Z","2019-02-11T23:55:59Z"];
            out meta;
            """,
            "should_pass": True,
        },
        # 16. Real-world: Statistical aggregation
        {
            "name": "Statistical Aggregation",
            "query": """
            [out:json][timeout:25];
            {{geocodeArea:"Zerniewicz, Jaraguá do Sul"}}->.searchArea;
            way["highway"](area.searchArea);
            for(t["highway"]) {
              make stat_highway_\\1 ,val=count(ways),sum=length(sum(length()));
            }
            out;
            """,
            "should_pass": True,
        },
        # 17. Real-world: Multi-layer administrative query
        {
            "name": "Multi-layer Administrative Query",
            "query": """
            [out:json][timeout:25];
            {{geocodeArea:"Budapest"}}->.searchArea;
            (relation["admin_level"="9"](area.searchArea););
            out;
            """,
            "should_pass": True,
        },
        # 18. Real-world: Pipeline query
        {
            "name": "Pipeline Query",
            "query": """
            [out:json][timeout:25];
            {{geocodeArea:"Hamburg"}}["admin_level"="4"]->.bndarea;
            node["amenity"="library"](area.bndarea);
            relation["amenity"="library"](area.bndarea);
            (area.bndarea;);>;
            out;
            """,
            "should_pass": True,
        },
        # 19. Real-world: Fuel station query
        {
            "name": "Fuel Station Query",
            "query": """
            [out:json][timeout:25];
            {{geocodeArea:""}}->.searchArea;
            way["amenity"="fuel"]["fuel:biogas"="yes"](area.searchArea);
            relation["amenity"="fuel"]["fuel:biogas"="yes"](area.searchArea);
            (area.searchArea;);>;
            out;
            """,
            "should_pass": True,
        },
        # 20. Real-world: Surface and length query
        {
            "name": "Surface and Length Query",
            "query": """
            [out:csv("surface","length")];
            {{geocodeArea:"Czerwienczyca"}}->.searchArea;
            way["highway"](area.searchArea);
            out;
            """,
            "should_pass": True,
        },
    ]

    print("Testing Complex Overpass QL Queries")
    print("=" * 60)

    passed = 0
    total = len(queries)

    for i, test in enumerate(queries, 1):
        print(f"\n--- Test {i}: {test['name']} ---")

        result = checker.check_syntax(test["query"])
        is_valid = result["valid"]
        should_pass = test["should_pass"]

        if is_valid == should_pass:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
            if should_pass:
                print("Expected: VALID, Got: INVALID")
                if result["errors"]:
                    print("Errors:")
                    for error in result["errors"][:3]:  # Show first 3 errors
                        print(f"  • {error}")
            else:
                print("Expected: INVALID, Got: VALID")

        # Show first few tokens for complex queries
        if len(test["query"].strip()) > 100:
            tokens = result.get("tokens", [])
            if tokens:
                print(f"Tokens (first 10): {', '.join(tokens[:10])}")

    print(f"\n{'=' * 60}")
    print(f"Complex Query Tests: {passed}/{total} passed ({passed / total * 100:.1f}%)")

    # Assert that all tests passed (for pytest)
    assert passed == total, f"Only {passed} out of {total} tests passed"


if __name__ == "__main__":
    test_complex_queries()
