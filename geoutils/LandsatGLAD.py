import argparse
import json
import os
import sys
import time
from pathlib import Path

import geopandas as gpd
import requests

from . import utils as ut


def main():
    """
    The function can be used to download the Landsat Analysis Ready Data (GLAD ARD)

    :param path_aoi: Path for AOI geojson.
    :param out_path: The list of available products.
    :param start_month: start month in specific year based on the code e.g. 24-May 2000 > 838 (int)
    :param end_month: end month in specific year based on code e.g. 12-Sep 2000 > 844 (int)
    :param count_years: how many years would like to download (int)
    :param username: username for GDAL account
    :param password: password for GDAL account
    :return: The saved images in the disk
    """
    parser = argparse.ArgumentParser(
        description="Landsat Analysis Ready Data (GLAD ARD)"
    )

    ### Determine the required variables ####
    parser.add_argument("--path_aoi", help="Path for AOI geojson. ", type=str)
    parser.add_argument("--out_path", help="The list of available products.", type=str)
    parser.add_argument(
        "--start_month",
        help="start month in specific year based on the code e.g. 24-May 2000 > 838 (int) ",
        type=int,
    )
    parser.add_argument(
        "--end_month",
        help="end month in specific year based on code e.g. 12-Sep 2000 > 844 (int) ",
        type=int,
    )
    parser.add_argument(
        "--count_years", help="how many years would like to download (int) ", type=int
    )
    parser.add_argument("--username", help="username for GDAL account ", type=str)
    parser.add_argument("--password", help="password for GDAL account ", type=str)

    args = parser.parse_args()
    out_path = args.out_path
    path_area_of_interest = args.path_aoi
    start_month = args.start_month
    end_month = args.end_month
    count_years = args.count_years
    password = args.password
    username = args.username

    region_geometry = ut.geometry_from_geojson(path_area_of_interest)
    xmin = region_geometry["coordinates"][0][0][0]
    xmax = region_geometry["coordinates"][0][2][0]
    ymin = region_geometry["coordinates"][0][0][1]
    ymax = region_geometry["coordinates"][0][2][1]
    bbox = (xmin, ymin, xmax, ymax)
    INPUT_DATA = Path(LandsatGLAD.__file__).parent / "data"  # type: ignore
    gdf = gpd.read_file(INPUT_DATA / "glad_landsat_tiles.geojson", bbox=bbox)

    tiles = list(gdf["TILE"])
    # Determine the list of the time range using the 16d_intervals.xls
    times = []
    start = start_month  # start:24-May 2000
    end = end_month + 1  # end:12-Sep 2000+ 1
    for i in range(count_years):  # Determine how many years would like to download
        times.extend(list(range(start, end)))
        start += 23
        end += 23

    # Downloading process
    url = "https://glad.umd.edu/dataset/landsat_v1.1/{lat}/{tile}/{interval}.tif"
    output = "{p}/{interval}.tif"

    for t in range(len(tiles)):
        for k in times:
            if not os.path.exists(out_path / tiles[t]):
                os.makedirs(out_path / tiles[t])

            if not os.path.exists(out_path / tiles[t] / (str(k) + ".tif")):
                r = requests.get(
                    url.format(lat=tiles[t][-3:], tile=tiles[t], interval=k),
                    auth=(username, password),
                )
                print(r.url)

                print(output.format(p=out_path / tiles[t], interval=k))
                open(output.format(p=out_path / tiles[t], interval=k), "wb").write(
                    r.content
                )


if __name__ == "__main__":
    main()
