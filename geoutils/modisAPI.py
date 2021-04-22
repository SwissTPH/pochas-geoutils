# Name: modisAPI.py
# Description: The tools to download the Modis data in NetCDF format
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date: 22.04.2021

# For requests
import requests
import numpy as np
from . import grid as gr
from . import utils as ut
from pyproj import Proj
import datetime as dt

# Utilities
from pathlib import Path
import time
import argparse
import sys
import os


def main():
    parser = argparse.ArgumentParser(description="MODIS and VIIRS Land Product Subsets RESTful Web Service")


    ### Determine the required variables ####
    parser.add_argument("--satellite", help="The list of available products.", type=str,
                        choices = ["MODIS-Terra", "MODIS-Aqua", "MODIS-TerraAqua", "VIIRS-SNPP", "Daymet", "SMAP", "ECOSTRESS"])

    parser.add_argument("--product", help=" Available band names for a product.", type=str)
    parser.add_argument("--band", help="Name of data layer. ", type=str)
    parser.add_argument("--startDate", help="Name of data layer. (YYYY-MM-DD') ", type=str)
    parser.add_argument("--endDate", help="Name of data layer. (YYYY-MM-DD') ", type=str)
    parser.add_argument("--path_aoi", help="Path for AOI geojson. ", type=str)
    parser.add_argument("--crs_aoi", help="Path for AOI geojson. Default: 4326 ", type=str,default="4326")


    args = parser.parse_args()
    satellite = args.satellite
    product = args.product
    band = args.band
    startDate = args.startDate
    endDate = args.endDate
    kmAboveBelow = 100
    kmLeftRight = 100

    path_area_of_interest = args.path_aoi
    if path_area_of_interest == None:
        print('Please enter AOI path')
        sys.exit()
    crs_area_of_interest = args.crs_aoi
    if crs_area_of_interest == None:
        print('Please enter CRS for the AOI')
        sys.exit()



    # Set subset parameters:
    url = "https://modis.ornl.gov/rst/api/v1/"
    header = {'Accept': 'application/json'}


    # list of available products.
    if satellite !=None:
        resp  = requests.get(url+f'/products?sensor={satellite}',headers=header)
        content = resp.json()
        for each in content['products']:
            print('%s: %s '%(each['product'],each['description']))

    #  retrieve available band names for a product
    if product!=None and band==None:
        resp = requests.get(url + f'{product}/bands', headers=header)
        content = resp.json()
        for each in content['bands']:
            print('%s: %s '%(each['band'],each['description']))

    # Get a list of dates using the dates function and parse to list of modis dates (i.e. AYYYYDOY):

    region_geometry = ut.geometry_from_geojson(path_area_of_interest)
    xmin = region_geometry['coordinates'][0][0][0]
    xmax = region_geometry['coordinates'][0][2][0]
    ymin = region_geometry['coordinates'][0][0][1]
    ymax = region_geometry['coordinates'][0][2][1]
    # https://gis.stackexchange.com/questions/190198/how-to-get-appropriate-crs-for-a-position-specified-in-lat-lon-coordinates
    zone = round((183+xmin)/6)
    if ymin > 0:
        EPSG = 32600+zone
    else:
        EPSG = 32700 + zone
    # https://ocefpaf.github.io/python4oceanographers/blog/2013/12/16/utm/
    Projection  = Proj(f"+proj=utm +zone={zone}K, +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
    UTMxMin,UTMyMin = Projection(xmin,ymin)
    UTMxMax, UTMyMax = Projection(xmax, ymax)

    area = (UTMxMax - UTMxMin) * (UTMyMax - UTMyMin)

    if area < 50000:
        cell_size = area
    elif area > 50000 and area < 100000:
        cell_size = 50000
    else:
        cell_size = 100000

    point_list_UTM = gr.grid(UTMxMin, UTMxMax, UTMyMin, UTMyMax, cell_size=cell_size, crs=EPSG).generate_point(center=True)
    point_list_WGS = np.asarray(Projection(point_list_UTM.X.values, point_list_UTM.Y.values, inverse=True)).T

    sd = dt.datetime.strptime(startDate, "%Y-%m-%d").date()
    ed = dt.datetime.strptime('endDate', "%Y-%m-%d").date()
    ab, lr = 100, 100


if __name__ == "__main__":
	main()

