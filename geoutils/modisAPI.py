# Name: modisAPI.py
# Description: The tools to download the Modis data in NetCDF format
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date: 22.04.2021
# https://github.com/ornldaac/modis-viirs-rest-api-python
# https://modis.ornl.gov/data/modis_webservice.html

# Utilities
import argparse
import datetime as dt
import json
import os
import sys
import time

import numpy as np
import requests
import rioxarray
import xarray as xr
from pyproj import CRS, Proj  # type: ignore

from . import grid as gr
from . import utils as ut


def main():
    """
    Download MODIS and VIIRS Land Product Subsets RESTful Web Service

    :param satellite: The list of available products.
    :param product: Available band names for a product.
    :param band: Name of data layer.
    :param startDate: Name of data layer. (YYYY-MM-DD')
    :param endDate: Name of data layer. (YYYY-MM-DD')
    :param path_aoi: Path for AOI geojson.
    :param crs_aoi: CRS for AOI geojson. Default: 4326
    :param ouput_crs: CRS for output. Default: 4326
    :param ouput_cellsize: out put image cellsize. Default: 250
    :param number_chunks: There is a limit of a maximum ten modis dates per reques. Default: 10
    :return: The saved images in the disk
    
    """
    parser = argparse.ArgumentParser(
        description="MODIS and VIIRS Land Product Subsets RESTful Web Service"
    )

    ### Determine the required variables ####
    parser.add_argument(
        "--satellite",
        help="The list of available products.",
        type=str,
        choices=[
            "MODIS-Terra",
            "MODIS-Aqua",
            "MODIS-TerraAqua",
            "VIIRS-SNPP",
            "Daymet",
            "SMAP",
            "ECOSTRESS",
        ],
    )

    parser.add_argument(
        "--product", help=" Available band names for a product.", type=str
    )
    parser.add_argument("--band", help="Name of data layer. ", type=str)
    parser.add_argument(
        "--startDate", help="Name of data layer. (YYYY-MM-DD') ", type=str
    )
    parser.add_argument(
        "--endDate", help="Name of data layer. (YYYY-MM-DD') ", type=str
    )
    parser.add_argument("--path_aoi", help="Path for AOI geojson. ", type=str)
    parser.add_argument(
        "--crs_aoi", help="CRS for AOI geojson. Default: 4326 ", type=int, default=4326
    )
    parser.add_argument(
        "--ouput_crs", help="CRS for output. Default: 4326 ", type=int, default=4326
    )
    parser.add_argument(
        "--ouput_cellsize",
        help="out put image cellsize. Default: 250 ",
        type=int,
        default=250,
    )
    parser.add_argument(
        "--number_chunks",
        help="There is a limit of a maximum ten modis dates per reques. Default: 10 ",
        type=int,
        default=10,
    )

    args = parser.parse_args()
    satellite = args.satellite
    product = args.product
    band = args.band

    # Set subset parameters:
    url = "https://modis.ornl.gov/rst/api/v1/"
    header = {"Accept": "application/json"}

    # list of available products.
    if args.satellite:
        # print(url + f'products?sensor={satellite}')
        resp = requests.get(url + f"/products?sensor={satellite}", headers=header)
        content = resp.json()
        time.sleep(5)
        for each in content["products"]:
            print("%s: %s " % (each["product"], each["description"]))

    #  retrieve available band names for a product
    if args.product:
        if band is None:
            resp = requests.get(url + f"{product}/bands", headers=header)
            content = resp.json()
            time.sleep(5)
            for each in content["bands"]:
                print("%s: %s " % (each["band"], each["description"]))
        else:
            # Get a list of data for product and band:

            path_area_of_interest = args.path_aoi
            if path_area_of_interest is None:
                print("Please enter AOI path")
                sys.exit()
            crs_area_of_interest = args.crs_aoi
            if crs_area_of_interest is None:
                print("Please enter CRS for the AOI")
                sys.exit()

            startDate = args.startDate
            if startDate is None:
                print("Please enter Start Date")
                sys.exit()
            endDate = args.endDate
            if endDate is None:
                print("Please enter End Date")
                sys.exit()

            ouput_crs = args.ouput_crs
            ouput_cellsize = args.ouput_cellsize
            number_chunks = args.number_chunks
            if number_chunks > 10 or number_chunks < 1:
                raise RuntimeError(f"Number should be between 1 and 10")

            region_geometry = ut.geometry_from_geojson(path_area_of_interest)
            xmin = region_geometry["coordinates"][0][0][0]
            xmax = region_geometry["coordinates"][0][2][0]
            ymin = region_geometry["coordinates"][0][0][1]
            ymax = region_geometry["coordinates"][0][2][1]
            # https://gis.stackexchange.com/questions/190198/how-to-get-appropriate-crs-for-a-position-specified-in-lat-lon-coordinates
            zone = round((183 + xmin) / 6)
            if ymin > 0:
                EPSG = 32600 + zone
            else:
                EPSG = 32700 + zone
            # https://ocefpaf.github.io/python4oceanographers/blog/2013/12/16/utm/
            Projection = Proj(
                f"+proj=utm +zone={zone}K, +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
            )
            UTMxMin, UTMyMin = Projection(xmin, ymin)
            UTMxMax, UTMyMax = Projection(xmax, ymax)

            sd = dt.datetime.strptime(startDate, "%Y-%m-%d").date()
            ed = dt.datetime.strptime(endDate, "%Y-%m-%d").date()
            ab, lr = 70, 70

            length = UTMxMax - UTMxMin
            width = UTMyMax - UTMyMin
            area = (length * width) / 1000000
            print(f"Area is equal to: {area} m2")
            if area < 50:
                print(f"The number of the tiles are: 1")
                point_long = UTMxMin + length / 2
                point_lat = UTMyMin + width / 2
                coords = np.asarray(Projection(point_long, point_lat, inverse=True)).T
                datesurl = [
                    url + f"{product}/dates?latitude={coords[1]}&longitude={coords[0]}"
                ]

                responses = [requests.get(date, headers=header) for date in datesurl]
                time.sleep(2)
                dates = [json.loads(resp.text)["dates"] for resp in responses]
                modis_dates = [
                    d["modis_date"]
                    for date in dates
                    for d in date
                    if all(
                        [
                            dt.datetime.strptime(d["calendar_date"], "%Y-%m-%d").date()
                            >= sd,
                            dt.datetime.strptime(d["calendar_date"], "%Y-%m-%d").date()
                            < ed,
                        ]
                    )
                ]

                chunks = list(ut.chunk(modis_dates, number_chunks))  # type: ignore
                subsets = []
                for i, c in enumerate(chunks):
                    print(
                        "[ "
                        + str(i + 1)
                        + " / "
                        + str(len(chunks))
                        + " ] "
                        + c[0]
                        + " - "
                        + c[-1]
                    )
                    _url = ut.getSubsetURL(
                        url, product, coords[1], coords[0], band, c[0], c[-1], ab, lr
                    )
                    _response = requests.get(_url, headers=header).json()
                    time.sleep(3)
                    subsets.append(_response)
                ut.convert_to_NetCDF(subsets, coords, ouput_crs, ouput_cellsize)

            else:
                grid_UTM = gr.grid(
                    UTMxMin, UTMxMax, UTMyMin, UTMyMax, cell_size=100000, crs=EPSG
                ).generate_grid()
                point_list_UTM = grid_UTM.centroid
                point_list_WGS = np.asarray(
                    Projection(
                        point_list_UTM.x.values, point_list_UTM.y.values, inverse=True
                    )
                ).T
                print(f"The number of the tiles are: {len(point_list_WGS)}")
                datesurl = [
                    url + f"{product}/dates?latitude={coord[0]}&longitude={coord[1]}"
                    for coord in point_list_WGS
                ]

                responses = [requests.get(date, headers=header) for date in datesurl]
                dates = [json.loads(resp.text)["dates"] for resp in responses]
                modis_dates = [
                    [
                        d["modis_date"]
                        for d in date
                        if all(
                            [
                                dt.datetime.strptime(
                                    d["calendar_date"], "%Y-%m-%d"
                                ).date()
                                >= sd,
                                dt.datetime.strptime(
                                    d["calendar_date"], "%Y-%m-%d"
                                ).date()
                                < ed,
                            ]
                        )
                    ]
                    for date in dates
                ]

                # divide modis_dates list into increments of 10
                # assemble url string from subset request parameters
                # Iterate over groups of dates, request subsets from the REST API, and append to a list of responses:
                for d, coords in enumerate(point_list_WGS):
                    print(f"coordinate: {coords}")
                    chunks = list(ut.chunk(modis_dates[d], number_chunks))  # type: ignore
                    subsets = []
                    for i, c in enumerate(chunks):
                        print(
                            "[ "
                            + str(i + 1)
                            + " / "
                            + str(len(chunks))
                            + " ] "
                            + c[0]
                            + " - "
                            + c[-1]
                        )
                        _url = ut.getSubsetURL(
                            url,
                            product,
                            coords[1],
                            coords[0],
                            band,
                            c[0],
                            c[-1],
                            ab,
                            lr,
                        )
                        _response = requests.get(_url, headers=header).json()
                        time.sleep(3)
                        subsets.append(_response)
                    ut.convert_to_NetCDF(subsets, coords, ouput_crs, ouput_cellsize)


if __name__ == "__main__":
    main()
