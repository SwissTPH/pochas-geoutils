# Name: dataExtraction.py
# Description: The tools to extract data from rasters
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date: 20.04.2021 Update:28.04.2021; 29.04.2021, 07.01.2022

from typing import List
import numpy as np
import numpy.ma as ma
import numpy.typing as npt
import pandas as pd
import geopandas as gpd
import rasterio as rs
from rasterio.io import MemoryFile
import xarray as xr
from affine import Affine
from . import utils as ut

# Func 01
def extract_geotif_to_point(
    rast_path: str,
    date: str,
    gdf_path: str,
    resample_size,
    stats: str = "mean",
    mask: bool = False,
    nodata: int = 0,
) -> gpd.GeoDataFrame:
    """
    The function extract the values for each date from GeoTIFF raster image

    :param rast_path: (file object or pathlib.Path object)
    :param date: when the raster collected (Form: dd_mm_yyyy). it is important for time series data
    :param gdf_path: (str, file object or pathlib.Path object)
    :param resample_size: The buffer around the points. For the the point zero should be used
    :param stats: The statistics should be used for aggregation
    :param mask: The nodata value would be masked; default:False
    :param nodata: value which should be consider as NoData value, default:0
    :return: gpd.GeoDataFrame
    """
    img = rs.open(rast_path)
    gdf = gpd.read_file(gdf_path)
    rowcol_tuple = img.index(gdf["geometry"].x, gdf["geometry"].y)
    rowcol = np.asarray(rowcol_tuple).T

    # Calcualte the pixel size of the image
    pixel_size = img.transform[0]

    if resample_size >= 0:
        size = int(np.floor((resample_size / pixel_size) / 2))
    else:
        raise RuntimeError(f"The sample size cannot be Negative")

    for b in img.indexes:
        band = img.read(b, out_dtype="float32")

        if stats == "mean":
            if size == 0:
                if mask == False:
                    extracted_values = ut.extract_point(band, rowcol)
                    gdf["b_" + str(b) + "_" + date] = extracted_values
                else:
                    raise RuntimeError(f"Extracting point cannot be with mask")
            else:
                if mask == False:
                    extracted_values = ut.extract_point_buffer(band, rowcol, size)
                    gdf["b_" + str(b) + "_" + date] = extracted_values
                else:
                    extracted_values = ut.extract_point_buffer_mask(
                        band, rowcol, size, nodata
                    )
                    gdf["b_" + str(b) + "_" + date] = extracted_values
        else:
            raise NameError(f"Mean only supported")

    return gdf


# Func 02:
def extract_netcdf_to_point(
    ds_path: str,
    gdf_path: str,
    resample_size: int,
    stats: str = "mean",
    mask: bool = False,
    nodata: int = -9999,
) -> gpd.GeoDataFrame:

    """
    The function extract the values for each date from NetCDF. Since the NetCDF files usually are multi-temporal
    it is decided to use multi process for each bands which can save a lot of time.

    :param rast_path: (str, file object or pathlib.Path object)
    :param gdf_path: (str, file object or pathlib.Path object)
    :param resample_size: The buffer around the points. For the the point zero should be used
    :param stats: The statistics should be used for aggregation
    :param mask: The nodata value would be masked; default:False
    :param nodata: value which should be consider as NoData value, default:0
    :return: gpd.GeoDataFrame
    """

    # Get the general info
    ds = xr.open_rasterio(ds_path)
    ds_xarray = xr.open_dataarray(ds_path)

    transform = Affine(*ds.attrs["transform"])
    count = ds.values.shape[0]
    height = ds.values.shape[1]
    width = ds.values.shape[2]
    dtype = ds.values.dtype
    pixel_size = ds.attrs["res"][0]

    if pixel_size > 1:
        crs = ds.attrs["crs"]
    else:
        crs = 4326

    # Define rasterio object in memory
    rast = MemoryFile().open(
        driver="GTiff",  # GDAL GeoTIFF driver
        count=count,  # number of bands
        height=height,  # length y
        width=width,  # length x
        crs=crs,  # srs
        dtype=dtype,  # data type
        nodata=nodata,  # fill value
        transform=transform,  # affine transformation
    )

    # Write a data to the raster
    rast.write(ds.values)

    # Prepare the points
    gdf = gpd.read_file(gdf_path)
    rowcol_tuple = rast.index(gdf["geometry"].x, gdf["geometry"].y)
    rowcol = np.asarray(rowcol_tuple).T

    if resample_size >= 0:
        size = int(np.floor((resample_size / pixel_size) / 2))
    else:
        raise RuntimeError(f"The sample size cannot be Negative")

    # Create a list of  dates
    lst_date = list(ds_xarray.indexes["time"].astype(str))
    # Help Function for parallelization
    for b, date in zip(rast.indexes, lst_date):
        band = rast.read(b, out_dtype="float32")
        if stats == "mean":
            if size == 0:
                if mask == False:
                    # print('b' + str(b) + "_" + date)
                    extracted_values = ut.extract_point(band, rowcol)
                    gdf[date] = extracted_values
                else:
                    raise RuntimeError(f"Extracting point cannot be with mask")
            else:
                if mask == False:
                    # print('b' + str(b) + "_" + date)
                    extracted_values = ut.extract_point_buffer(band, rowcol, size)
                    gdf[date] = extracted_values
                else:
                    # print('b' + str(b) + "_" + date)
                    extracted_values = ut.extract_point_buffer_mask(
                        band, rowcol, size, nodata
                    )
                    gdf[date] = extracted_values
        else:
            raise NameError(f"Mean only supported")

    return gdf


def extract_class(image: npt.ArrayLike, codes: List[int], new_code: int):
    """
    This function split different high-level classes based on
    the sub-classes

    :param image: The original image to extract the groups 
    :param codes: The list of the codes which should be extracted 
    :param new_code: The code which should be determined to the new class
    :return: npt.ArrayLike
    """

    mask = np.isin(image, codes) * image  # Mask the agricultural areas
    category = np.where(
        np.isin(mask, codes), new_code, 0
    )  # Convert the mask to the binary image
    return category
