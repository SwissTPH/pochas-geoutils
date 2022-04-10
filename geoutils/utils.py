import datetime as dt
import json
import os

import numpy as np
import numpy.ma as ma
import rioxarray
import xarray as xr
from pyproj import CRS, Proj  # type: ignore


# ModisAPI.py utils:
def geometry_from_geojson(filepath: str):
    with open(filepath, "r") as f:
        json_obj = json.load(f)

    geojson_type = json_obj["type"]
    if geojson_type == "FeatureCollection":
        features = json_obj["features"]
        if len(features) == 0:
            raise IOError(f"No features contained in {filepath}")
        elif len(features) > 1:
            raise IOError(
                f"More than one feature contained in {filepath}, must be exactly 1"
            )

        feature = features[0]
        ftype = feature["geometry"]["type"]
        if ftype not in ["Polygon", "MultiPolygon"]:
            raise IOError(
                f"Feature type in {filepath} must be either Polygon or MultiPolygon"
            )

        return feature["geometry"]

    elif geojson_type in ["Polygon", "MultiPolygon"]:
        return json_obj
    else:
        raise IOError(
            f"Feature type in {filepath} must be either FeatureCollection, Polygon or MultiPolygon"
        )


"""yield successive n-sized chunks from list l"""


def chunk(l: int, n: int):
    for i in range(0, len(l), n):  # type: ignore
        yield l[i : i + n]  # type: ignore


"""assemble request URL string"""


def getSubsetURL(
    url: str,
    prod: str,
    lat: float,
    lon: float,
    band: int,
    sd: str,
    ed: str,
    ab: float,
    lr: float,
):
    return "".join(
        [
            url,
            prod,
            "/subset?",
            "latitude=",
            str(lat),
            "&longitude=",
            str(lon),
            "&band=",
            str(band),
            "&startDate=",
            str(sd),
            "&endDate=",
            str(ed),
            "&kmAboveBelow=",
            str(ab),
            "&kmLeftRight=",
            str(lr),
        ]
    )


def convert_to_NetCDF(subsets, coords, ouput_crs, ouput_cellsize):
    # Use dictionary comprehension to get some spatial metadata from the first subset in our list:
    meta = {key: value for key, value in subsets[0].items() if key != "subset"}
    # Iterate over the list of subsets and collect the data in a dictionary:
    data = {"dates": [], "arrays": []}
    for i in subsets:
        for j in i["subset"]:
            data["dates"].append(j["calendar_date"])
            data["arrays"].append(
                np.array(j["data"]).reshape(meta["nrows"], meta["ncols"])
            )

    # Use the metadata to make lists of x and y coordinates:
    # f(ncols,nrows): n * cellsize + corner_coordinate
    dtdates = [dt.datetime.strptime(d, "%Y-%m-%d") for d in data["dates"]]
    xcoordinates = [float(meta["xllcorner"])] + [
        i * meta["cellsize"] + float(meta["xllcorner"]) for i in range(1, meta["ncols"])
    ]
    ycoordinates = [float(meta["yllcorner"])] + [
        i * meta["cellsize"] + float(meta["yllcorner"]) for i in range(1, meta["nrows"])
    ]
    # Make an xarray.DataArray object:

    xrDataArray = xr.DataArray(
        name=meta["band"],
        data=np.flipud(np.dstack(data["arrays"])),
        coords=[np.array(ycoordinates), np.array(xcoordinates), dtdates],  # type: ignore
        dims=["y", "x", "time"],
        attrs=dict(units=meta["units"]),
    )
    # Finally, save as netCDF:
    xrDataArray_T = xrDataArray.transpose("time", "y", "x")
    crs = "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m"
    xrDataArray_CRS = xrDataArray_T.rio.write_crs(crs)

    if ouput_crs != 4326:
        if ouput_cellsize is None:
            raise RuntimeError(f"Please determine the cell size for projection")
        else:

            file = xrDataArray_CRS.rio.reproject(
                f"epsg:{ouput_crs}", resolution=ouput_cellsize
            )
    else:
        file = xrDataArray_CRS.rio.reproject(f"epsg:{ouput_crs}")

    xrDataArray_CRS.to_netcdf(
        f"output_{coords[0]}_{coords[1]}.nc", unlimited_dims="time", engine="netcdf4"
    )


# Define the help function to be used in the main function
def extract_point(b, rc):
    """
    Extract the value for the points
    """
    extracted_values = [b[coord[0], coord[1]] for coord in rc]
    return extracted_values


def extract_point_buffer(b, rc, s):
    """
    Extract the value based on the surrounded buffer
    """
    extracted_values = [
        np.mean(b[coord[0] - s : coord[0] + (s + 1), coord[1] - s : coord[1] + (s + 1)])
        for coord in rc
    ]
    return extracted_values


def extract_point_buffer_mask(b, rc, s, nd):
    """
    Extract the value based on the surrounded buffer and mask the nodata value in calculation
    """
    extracted_values = [
        np.nanmean(
            ma.masked_values(
                b[coord[0] - s : coord[0] + (s + 1), coord[1] - s : coord[1] + (s + 1)],
                nd,
            ).filled(np.nan)
        )
        for coord in rc
    ]
    return extracted_values


def list_files_with_absolute_paths(dirpath: str, endswith: str = None):  # type: ignore
    if endswith is None:
        files = []
        for dirname, dirnames, filenames in os.walk(dirpath):
            files += [os.path.join(dirname, filename) for filename in filenames]
    else:
        files = []
        for dirname, dirnames, filenames in os.walk(dirpath):
            files += [
                os.path.join(dirname, filename)
                for filename in filenames
                if filename.endswith(endswith)
            ]
    return files


def list_files(dirpath: str, endswith: str = None):  # type: ignore
    if endswith is not None:
        files = []
        for dirname, dirnames, filenames in os.walk(dirpath):
            files += [filename for filename in filenames if filename.endswith(endswith)]
    else:
        files = []
        for dirname, dirnames, filenames in os.walk(dirpath):
            files += [filename for filename in filenames]
    return files

