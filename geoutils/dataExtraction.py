# Name: dataExtraction.py
# Description: The tools to extract data from rasters
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date: 20.04.2021 Update:28.04.2021; 29.04.2021

import numpy as np
import numpy.ma as ma
import pandas as pd
import geopandas as gpd
import rasterio as rs
from rasterio.io import MemoryFile
import xarray as xr
from affine import Affine
from . import utils as ut

# Func 01
def extract_geotif_to_point(rast_path,date,gdf_path,resample_size,stats='mean',mask=False,nodata=0):
    """
    rast_path: (str, file object or pathlib.Path object)
    gdf_path: (str, file object or pathlib.Path object)
    date: when the raster collected (str): dd_mm_yyyy. it is important for time series data
    resample_size: The buffer around the points. For the the point zero should be used
    stats: The statistics should be used for aggregation
    mask: The nodata value would be masked; default:False
    nodata
    """
    img = rs.open(rast_path)
    gdf = gpd.read_file(gdf_path)
    rowcol_tuple = img.index(gdf['geometry'].x, gdf['geometry'].y)
    rowcol = np.asarray(rowcol_tuple).T

    # Calcualte the pixel size of the image
    pixel_size = img.transform[0]

    if resample_size > 0:
        size = int(np.floor((resample_size/pixel_size)/2))
    elif resample_size == 0:
        pass
    else:
        raise RuntimeError(f"The sample size cannot be Negative")

    for b in img.indexes:
        band = img.read(b,out_dtype='float32')

        if stats == "mean":
            if size == 0:
                if mask == False:
                    extracted_values = ut.extract_point(band,rowcol)
                    gdf['band_' + str(b) + "_" + date] = extracted_values
                else:
                    raise RuntimeError(f"Extracting point cannot be with mask")
            else:
                if mask == False:
                    extracted_values = ut.extract_point_buffer(band,rowcol,size)
                    gdf['band_'+ str(b) + "_" + date] = extracted_values
                else:
                    extracted_values = ut.extract_point_buffer_mask(band, rowcol, size,nodata)
                    gdf['band_' + str(b) + "_" + date] = extracted_values
        else:
            raise NameError(f"Mean only supported")

    return gdf

# Func 02:
def extract_netcdf_to_point(ds_path,gdf_path,resample_size,stats='mean',mask=False,nodata=-9999):

    """
    The function extract the values for each date from NetCDF. Since the NetCDF files usually are multi-temporal
    it is decided to use multi process for each bands which can save a lot of time.

    rast_path: (str, file object or pathlib.Path object)
    gdf_path: (str, file object or pathlib.Path object)
    resample_size: The buffer around the points. For the the point zero should be used
    stats: The statistics should be used for aggregation
    mask: The nodata value would be masked; default:False
    nodata: value which should be consider as NoData value
    """

    # Get the general info
    ds = xr.open_rasterio(ds_path)
    ds_xarray = xr.open_dataarray(ds_path)

    transform = Affine(*ds.attrs['transform'])
    count = ds.values.shape[0]
    height = ds.values.shape[1]
    width = ds.values.shape[2]
    dtype= ds.values.dtype
    pixel_size = ds.attrs['res'][0]

    if pixel_size  > 1:
        crs = ds.attrs['crs']
    else:
        crs = 4326

    # Define rasterio object in memory
    rast = MemoryFile().open(
        driver='GTiff',  # GDAL GeoTIFF driver
        count=count,  # number of bands
        height=height,  # length y
        width=width,  # length x
        crs=crs,  # srs
        dtype=dtype,  # data type
        nodata=nodata,  # fill value
        transform=transform  # affine transformation
    )

    # Write a data to the raster
    rast.write(ds.values)

    # Prepare the points
    gdf = gpd.read_file(gdf_path)
    rowcol_tuple = rast.index(gdf['geometry'].x, gdf['geometry'].y)
    rowcol = np.asarray(rowcol_tuple).T

    if resample_size >= 0:
        size = int(np.floor((resample_size/pixel_size)/2))
    else:
        raise RuntimeError(f"The sample size cannot be Negative")

    # Create a list of  dates
    lst_date = list(ds_xarray.indexes['time'].astype(str))
    # Help Function for parallelization
    for b,date in zip(rast.indexes,lst_date):
        band = rast.read(b, out_dtype='float32')
        if stats == "mean":
            if size == 0:
                if mask == False:
                    # print('b' + str(b) + "_" + date)
                    extracted_values = ut.extract_point(band,rowcol)
                    gdf[date] = extracted_values
                else:
                    raise RuntimeError(f"Extracting point cannot be with mask")
            else:
                if mask == False:
                    # print('b' + str(b) + "_" + date)
                    extracted_values = ut.extract_point_buffer(band,rowcol,size)
                    gdf[date] = extracted_values
                else:
                    # print('b' + str(b) + "_" + date)
                    extracted_values = ut.extract_point_buffer_mask(band, rowcol, size,nodata)
                    gdf[date] = extracted_values
        else:
            raise NameError(f"Mean only supported")

    return gdf

