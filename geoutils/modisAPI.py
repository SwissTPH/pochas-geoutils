# Name: modisAPI.py
# Description: The tools to download the Modis data in NetCDF format
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date: 22.04.2021

# For requests
import requests, json, os
import numpy as np
from . import grid as gr
from . import utils as ut
from pyproj import Proj, CRS
import datetime as dt
import xarray as xr
import rioxarray

# Utilities
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="MODIS and VIIRS Land Product Subsets RESTful Web Service")

    ### Determine the required variables ####
    parser.add_argument("--satellite", help="The list of available products.", type=str,
                        choices=["MODIS-Terra", "MODIS-Aqua", "MODIS-TerraAqua", "VIIRS-SNPP", "Daymet", "SMAP",
                                 "ECOSTRESS"])

    parser.add_argument("--product", help=" Available band names for a product.", type=str)
    parser.add_argument("--band", help="Name of data layer. ", type=str)
    parser.add_argument("--startDate", help="Name of data layer. (YYYY-MM-DD') ", type=str)
    parser.add_argument("--endDate", help="Name of data layer. (YYYY-MM-DD') ", type=str)
    parser.add_argument("--path_aoi", help="Path for AOI geojson. ", type=str)
    parser.add_argument("--crs_aoi", help="Path for AOI geojson. Default: 4326 ", type=str, default="4326")

    args = parser.parse_args()
    satellite = args.satellite
    product = args.product
    band = args.band
    startDate = args.startDate
    endDate = args.endDate
    kmAboveBelow = 100
    kmLeftRight = 100

    path_area_of_interest = args.path_aoi
    if path_area_of_interest is None:
        print('Please enter AOI path')
        sys.exit()
    crs_area_of_interest = args.crs_aoi
    if crs_area_of_interest is None:
        print('Please enter CRS for the AOI')
        sys.exit()

    # Set subset parameters:
    url = "https://modis.ornl.gov/rst/api/v1/"
    header = {'Accept': 'application/json'}

    # list of available products.
    if satellite is not None:
        resp = requests.get(url + f'/products?sensor={satellite}', headers=header)
        content = resp.json()
        for each in content['products']:
            print('%s: %s ' % (each['product'], each['description']))

    #  retrieve available band names for a product
    if product is not None and band is None:
        resp = requests.get(url + f'{product}/bands', headers=header)
        content = resp.json()
        for each in content['bands']:
            print('%s: %s ' % (each['band'], each['description']))

    # Get a list of dates using the dates function and parse to list of modis dates (i.e. AYYYYDOY):

    region_geometry = ut.geometry_from_geojson(path_area_of_interest)
    xmin = region_geometry['coordinates'][0][0][0]
    xmax = region_geometry['coordinates'][0][2][0]
    ymin = region_geometry['coordinates'][0][0][1]
    ymax = region_geometry['coordinates'][0][2][1]
    # https://gis.stackexchange.com/questions/190198/how-to-get-appropriate-crs-for-a-position-specified-in-lat-lon-coordinates
    zone = round((183 + xmin) / 6)
    if ymin > 0:
        EPSG = 32600 + zone
    else:
        EPSG = 32700 + zone
    # https://ocefpaf.github.io/python4oceanographers/blog/2013/12/16/utm/
    Projection = Proj(f"+proj=utm +zone={zone}K, +south +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
    UTMxMin, UTMyMin = Projection(xmin, ymin)
    UTMxMax, UTMyMax = Projection(xmax, ymax)

    # TODO: consider center if the area is less than 100KM2
    length = (UTMxMax - UTMxMin)
    width = (UTMyMax - UTMyMin)
    area = length * width
    if area < 100000:
        cell_size = max(np.floor(length), np.floor(width))

    grid_UTM = gr.grid(UTMxMin, UTMxMax, UTMyMin, UTMyMax, cell_size=100000, crs=EPSG).generate_grid()
    point_list_UTM = grid_UTM.centroid
    point_list_WGS = np.asarray(Projection(point_list_UTM.x.values, point_list_UTM.y.values, inverse=True)).T

    sd = dt.datetime.strptime(startDate, "%Y-%m-%d").date()
    ed = dt.datetime.strptime(endDate, "%Y-%m-%d").date()
    ab, lr = 50, 50

    datesurl = [url + f'{product}/dates?latitude={coord[0]}&longitude={coord[1]}' for coord in point_list_WGS]
    responses = [requests.get(date, headers=header) for date in datesurl]
    dates = [json.loads(resp.text)['dates'] for resp in responses]
    modis_dates = [
        [d['modis_date'] for d in date if all([dt.datetime.strptime(d['calendar_date'], "%Y-%m-%d").date() >= sd,
                                               dt.datetime.strptime(d['calendar_date'], "%Y-%m-%d").date() < ed])] for
        date in dates]

    # divide modis_dates list into increments of 10
    # assemble url string from subset request parameters
    # Iterate over groups of dates, request subsets from the REST API, and append to a list of responses:
    # TODO: add ut.foo for the help functions and change the prod to product
    for d, coords in enumerate(point_list_WGS):
        print(f'coordinate: {coords}')
        chunks = list(chunk(modis_dates[d], 10))
        subsets = []
        for i, c in enumerate(chunks):
            print("[ " + str(i + 1) + " / " + str(len(chunks)) + " ] " + c[0] + " - " + c[-1])
            _url = getSubsetURL(prod, coords[1], coords[0], band, c[0], c[-1], ab, lr)
            _response = requests.get(_url, headers=header)
            subsets.append(json.loads(_response.text))

        # Use dictionary comprehension to get some spatial metadata from the first subset in our list:
        meta = {key: value for key, value in subsets[0].items() if key != "subset"}
        # Iterate over the list of subsets and collect the data in a dictionary:
        data = {'dates': [], 'arrays': []}
        for i in subsets:
            for j in i['subset']:
                data['dates'].append(j['calendar_date'])
                data['arrays'].append(np.array(j['data']).reshape(meta['nrows'], meta['ncols']))

        # Use the metadata to make lists of x and y coordinates:
        # f(ncols,nrows): n * cellsize + corner_coordinate
        dtdates = [dt.datetime.strptime(d, "%Y-%m-%d") for d in data['dates']]
        xcoordinates = [float(meta['xllcorner'])] + [i * meta['cellsize'] + float(meta['xllcorner']) for i in
                                                     range(1, meta['ncols'])]
        ycoordinates = [float(meta['yllcorner'])] + [i * meta['cellsize'] + float(meta['yllcorner']) for i in
                                                     range(1, meta['nrows'])]
        # Make an xarray.DataArray object:

        xrDataArray = xr.DataArray(
            name=meta['band'],
            data=np.flipud(np.dstack(data['arrays'])),
            coords=[np.array(ycoordinates), np.array(xcoordinates), dtdates],
            dims=["y", "x", "time"],
            attrs=dict(units=meta['units'])
        )
        # Finally, save as netCDF:
        xrDataArray_T = xrDataArray.transpose("time", "y", "x")
        crs = CRS.from_proj4("+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m")
        xrDataArray_CRS = xrDataArray_T.rio.write_crs(crs)
        file = xrDataArray_CRS.rio.reproject("epsg:3035", resolution=250)

        file.rio.to_raster(f'output_{coords[0]}_{coords[1]}.tif')
#ToDO: Add variable to define the out put CRS
#TODO: Filter the data between -2000 to 10000 and consider -3000 as NoData Value
if __name__ == "__main__":
    main()
