# Name: image.py
# Description: The tools to work with raster data
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date:27.01.2022


import os
from pathlib import Path, PosixPath
from typing import Set

import pandas as pd
import rasterio as rs
import rioxarray
import xarray as xr
from rioxarray.merge import merge_arrays

from . import utils as ut


def mosaic_from_tiles(
    in_put_path: str,
    out_put_path: str,
    dtype: str = "float32",
    nodata: int = -9999,
    mask: int = None,  # type: ignore
    format: str = "GeoTiff",
):
    """
    The function generate a mosaic from the tiles. All the tiles should be in the same projection

    :param in_put_path: The path to tiles
    :param out_put_path: Output path to save the generated mosaic
    :param dtype: data type
    :param nodata: NAN value which should be assigned
    :param format: Image format can be GeoTIFF or NetCDF
    :return: The saved image in the disk
    """
    in_path = Path(in_put_path)
    out_path = Path(out_put_path)

    img_list = ut.list_files_with_absolute_paths(in_path, endswith=".tif")  # type: ignore
    if format is "GeoTiff":
        img_list = ut.list_files_with_absolute_paths(in_path, endswith=".tif")  # type: ignore
        img_series = [xr.open_rasterio(img) for img in img_list]
    else:
        img_list = ut.list_files_with_absolute_paths(in_path, endswith=".nc")  # type: ignore
        img_series = [xr.open_dataarray(img) for img in img_list]

    merged = merge_arrays(img_series)
    if mask is not None:
        merged = merged.where(merged != mask, nodata)  # type: ignore

    merged.rio.set_nodata(input_nodata=nodata, inplace=True)
    if format is "GeoTiff":
        merged.rio.to_raster(out_path / "mosaic_image.tif", dtype=dtype)
    else:
        merged.to_netcdf("mosaic_image.nc", unlimited_dims="time", engine="netcdf4")
    print("Mosaic is created!")


def exract_boundry(original_img: str, source_img: str, out_path: str, crs: str):
    """
    The function allign the original image with source image

    :param original_img: The image should be mapped to the source image
    :param source_image: The image which should not be changed
    :param out_path: Output path to save the image
    :param crs: the output image projection
    :return: The saved image in the disk
    """
    original_ = rs.open(original_img)
    source_ = rs.open(source_img)
    minx, miny, maxx, maxy = source_.bounds
    window = from_bounds(minx, miny, maxx, maxy, transform=original_.transform) # type: ignore
    width = source_.width
    height = source_.height
    transform = rs.transform.from_bounds(minx, miny, maxx, maxy, width, height) # type: ignore
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

