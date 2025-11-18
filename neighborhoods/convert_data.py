#!/usr/bin/env python3
"""
Convert neighborhood_centroids_with_od.geojson into separate files:
1. neighborhood_centroids.geojson (geometry only)
2. data/YYYY-MM.json (ride data only)
"""

import json
import sys
from datetime import datetime

def convert_centroids_with_od(input_file, output_geojson, output_data_json, month_id):
    """
    Convert a centroids GeoJSON with OD data into separate files.
    
    Args:
        input_file: Path to neighborhood_centroids_with_od.geojson
        output_geojson: Path for output geometry-only GeoJSON
        output_data_json: Path for output data JSON
        month_id: Month identifier (e.g., '2024-10')
    """
    
    # Load input file
    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        geojson = json.load(f)
    
    # Create geometry-only GeoJSON
    geometry_geojson = {
        "type": "FeatureCollection",
        "name": "neighborhood_centroids",
        "features": []
    }
    
    # Create data structure
    data = {
        "month": month_id,
        "generated": datetime.now().strftime("%Y-%m-%d"),
        "neighborhoods": {}
    }
    
    # Process each feature
    for feature in geojson['features']:
        props = feature['properties']
        nhood = props.get('nhood')
        
        if not nhood:
            print(f"Warning: Feature without 'nhood' property, skipping")
            continue
        
        # Add geometry-only feature
        geometry_geojson['features'].append({
            "type": "Feature",
            "properties": {
                "nhood": nhood
            },
            "geometry": feature['geometry']
        })
        
        # Extract data
        data['neighborhoods'][nhood] = {
            "total_starts": props.get('total_starts', 0),
            "total_ends": props.get('total_ends', 0),
            "destinations": props.get('destinations', {}),
            "origins": props.get('origins', {})
        }
    
    # Write geometry file
    print(f"Writing geometry to {output_geojson}...")
    with open(output_geojson, 'w') as f:
        json.dump(geometry_geojson, f, indent=2)
    
    # Write data file
    print(f"Writing data to {output_data_json}...")
    with open(output_data_json, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Print statistics
    print(f"\nConversion complete!")
    print(f"  Neighborhoods processed: {len(data['neighborhoods'])}")
    print(f"  Geometry file size: {len(json.dumps(geometry_geojson))} bytes")
    print(f"  Data file size: {len(json.dumps(data))} bytes")
    
    # Calculate total rides
    total_starts = sum(n['total_starts'] for n in data['neighborhoods'].values())
    total_ends = sum(n['total_ends'] for n in data['neighborhoods'].values())
    print(f"  Total rides starting: {total_starts:,}")
    print(f"  Total rides ending: {total_ends:,}")


def convert_neighborhoods_with_od(input_file, output_geojson):
    """
    Convert neighborhoods GeoJSON with OD data to geometry-only version.
    
    Args:
        input_file: Path to neighborhoods_with_od.geojson
        output_geojson: Path for output geometry-only GeoJSON
    """
    
    # Load input file
    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        geojson = json.load(f)
    
    # Create geometry-only GeoJSON
    geometry_geojson = {
        "type": "FeatureCollection",
        "name": "neighborhoods",
        "features": []
    }
    
    # Process each feature
    for feature in geojson['features']:
        props = feature['properties']
        nhood = props.get('nhood')
        
        if not nhood:
            print(f"Warning: Feature without 'nhood' property, skipping")
            continue
        
        # Add geometry-only feature
        geometry_geojson['features'].append({
            "type": "Feature",
            "properties": {
                "nhood": nhood
            },
            "geometry": feature['geometry']
        })
    
    # Write geometry file
    print(f"Writing geometry to {output_geojson}...")
    with open(output_geojson, 'w') as f:
        json.dump(geometry_geojson, f, indent=2)
    
    print(f"\nConversion complete!")
    print(f"  Neighborhoods processed: {len(geometry_geojson['features'])}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Convert centroids with OD data:")
        print("    python convert_data.py centroids <input.geojson> <output.geojson> <data.json> <YYYY-MM>")
        print("  Convert neighborhoods with OD data:")
        print("    python convert_data.py neighborhoods <input.geojson> <output.geojson>")
        print("\nExamples:")
        print("  python convert_data.py centroids neighborhood_centroids_with_od.geojson neighborhood_centroids.geojson data/2024-10.json 2024-10")
        print("  python convert_data.py neighborhoods neighborhoods_with_od.geojson neighborhoods.geojson")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "centroids":
        if len(sys.argv) != 6:
            print("Error: centroids command requires 4 arguments")
            print("Usage: python convert_data.py centroids <input.geojson> <output.geojson> <data.json> <YYYY-MM>")
            sys.exit(1)
        
        convert_centroids_with_od(
            sys.argv[2],  # input file
            sys.argv[3],  # output geojson
            sys.argv[4],  # output data json
            sys.argv[5]   # month id
        )
    
    elif command == "neighborhoods":
        if len(sys.argv) != 4:
            print("Error: neighborhoods command requires 2 arguments")
            print("Usage: python convert_data.py neighborhoods <input.geojson> <output.geojson>")
            sys.exit(1)
        
        convert_neighborhoods_with_od(
            sys.argv[2],  # input file
            sys.argv[3]   # output geojson
        )
    
    else:
        print(f"Error: Unknown command '{command}'")
        print("Valid commands: centroids, neighborhoods")
        sys.exit(1)
