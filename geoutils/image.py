# Name: image.py
# Description: The tools to work with raster data
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date:27.01.2022


import xarray as xr
import rioxarray
from rioxarray.merge import merge_arrays
import rasterio as rs
import pandas as pd
from pathlib import Path, PosixPath
import os
from . import utils as ut
from typing import Set


def mosaic_from_tiles(
    in_put_path: str,
    out_put_path: str,
    dtype: str = "float32",
    nodata: int = -9999,
    mask: int = None,
    format: str = "GeoTiff",
):
    in_path = Path(in_put_path)
    out_path = Path(out_put_path)

    img_list = ut.list_files_with_absolute_paths(in_path, endswith=".tif")
    if format is "GeoTiff":
        img_list = ut.list_files_with_absolute_paths(in_path, endswith=".tif")
        img_series = [xr.open_rasterio(img) for img in img_list]
    else:
        img_list = ut.list_files_with_absolute_paths(in_path, endswith=".nc")
        img_series = [xr.open_dataarray(img) for img in img_list]

    merged = merge_arrays(img_series)
    if mask is not None:
        merged = merged.where(merged != mask, nodata)

    merged.rio.set_nodata(input_nodata=nodata, inplace=True)
    if format is "GeoTiff":
        merged.rio.to_raster(out_path / "mosaic_image.tif", dtype=dtype)
    else:
        merged.to_netcdf("mosaic_image.nc", unlimited_dims="time", engine="netcdf4")
    print("Mosaic is created!")


def exract_boundry(original_img: str, source_img: str, out_path: str, crs: str):
    """
    The function 
    original_img: The image should be mapped to the source image
    source_image: The image which should not be changed
    """
    original_ = rs.open(original_img)
    source_ = rs.open(source_img)
    minx, miny, maxx, maxy = source_.bounds
    window = from_bounds(minx, miny, maxx, maxy, transform=original_.transform)
    width = source_.width
    height = source_.height
    transform = rs.transform.from_bounds(minx, miny, maxx, maxy, width, height)
    result = original_.read(window=window, out_shape=(height, width), resampling=0)
    out_path = out_path
    with rs.open(
        out_path,
        "w",
        driver="GTiff",
        count=1,
        transform=transform,
        width=width,
        height=height,
        dtype=result.dtype,
        crs=crs,
    ) as output_file:
        output_file.write(result)
