import json

def geometry_from_geojson(filepath):
    with open(filepath, 'r') as f:
        json_obj = json.load(f)

    geojson_type = json_obj["type"]
    if geojson_type == 'FeatureCollection':
        features = json_obj['features']
        if len(features) == 0:
            raise IOError(f"No features contained in {filepath}")
        elif len(features) > 1:
            raise IOError(f"More than one feature contained in {filepath}, must be exactly 1")

        feature = features[0]
        ftype = feature['geometry']['type']
        if ftype not in ['Polygon', 'MultiPolygon']:
            raise IOError(f"Feature type in {filepath} must be either Polygon or MultiPolygon")

        return feature['geometry']

    elif geojson_type in ['Polygon', 'MultiPolygon']:
        return json_obj
    else:
        raise IOError(f"Feature type in {filepath} must be either FeatureCollection, Polygon or MultiPolygon")



