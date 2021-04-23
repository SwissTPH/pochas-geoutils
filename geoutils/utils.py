import json,os

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




"""yield successive n-sized chunks from list l"""
def chunk(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

"""assemble request URL string"""
def getSubsetURL( url, prod , lat , lon , band, sd , ed , ab , lr ): return( "".join([
    url, prod, "/subset?",
    "latitude=", str(lat),
    "&longitude=", str(lon),
    "&band=", str(band),
    "&startDate=", str(sd),
    "&endDate=", str(ed),
    "&kmAboveBelow=", str(ab),
    "&kmLeftRight=", str(lr) ]) )


def list_files_with_absolute_paths(dirpath,endswith=None):
    if endswith is None:
        files = []
        for dirname, dirnames, filenames in os.walk(dirpath):
            files += [os.path.join(dirname, filename) for filename in filenames]
    else:
        files = []
        for dirname, dirnames, filenames in os.walk(dirpath):
            files += [os.path.join(dirname, filename) for filename in filenames if filename.endswith(endswith)]
    return files

def list_files(dirpath,endswith=None):
    if endswith is not None:
        files = []
        for dirname, dirnames, filenames in os.walk(dirpath):
            files += [filename for filename in filenames if filename.endswith(endswith)]
    else:
        files = []
        for dirname, dirnames, filenames in os.walk(dirpath):
            files += [filename for filename in filenames]
    return files
