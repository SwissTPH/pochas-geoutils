# Name: cube.py
# Description: The tools to generate a cube from rasters, plus it includes some functions to work with images
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date: 07.04.2021
# Update: 23.04.2021; 04.05.2021


import xarray as xr
import rioxarray
from rioxarray.merge import merge_arrays
import rasterio as rs
import pandas as pd
from pathlib import Path, PosixPath
import os
from . import utils as ut
from typing import Set, List, Optional


def get_imgs(
    img_list: List[str], chunks: Set[int] = (1000, 1000)
) -> List[xr.DataArray]:
    """
    Opens the rasters as Dask dataArray

    :param img_list: The list of the image name/path
    :param chunks: The chunk size
    :return: list of the opend images (list)
    """
    series = [
        xr.open_rasterio(i, chunks={"x": chunks[0], "y": chunks[1]}) for i in img_list
    ]
    return series


class cube:
    def __init__(self, rast_list):
        """
        To generate the data cube from individual raster files. The list can be generated using `get_imgs` function

        :param rast_list: The list of the xarray.DataArray 
        """
        self.rast_list = rast_list

    # Func 01
    def generate_cube(self, start_date: str, freq: str):
        """
        Generate a data cube from the list of the xarray.DataArray 

        :param start_date: The first raster acqusition date
        :param start_date: Frequency to collect the image
        :return: xarray.DataArray
        """
        # Concatenate image series
        concat_img = xr.concat(self.rast_list, "time")
        # Add variable name
        concat_img = concat_img.rename("raster")
        # Add timestamp to data
        time = pd.date_range(start=start_date, periods=len(self.rast_list), freq=freq)
        concat_img = concat_img.assign_coords({"time": time})
        return concat_img

    # Func 02
    def generate_mosaic(self):
        # Todo: median is not yet implemented on dask arrays, otherwise it is possible to use `group by` method to do this part
        """
        Generate the mosaic with calculation median over time from the list of the xarray.DataArray 

        :return: xarray.DataArray
        """
        no_of_bands = max(self.rast_list[0].coords["band"].values)
        crs = int(self.rast_list[0].attrs["crs"][-4:])

        bands_medians = []
        for b in range(no_of_bands):
            bands = [rast.sel(band=b + 1) for rast in self.rast_list]
            bands_comp = xr.concat(bands, dim="band")
            bands_medians.append(bands_comp.median(dim="band", skipna=True))

        bands_medians_cont = xr.concat(bands_medians, dim="band")
        crs_img = bands_medians_cont.rio.write_crs(crs)
        return crs_img


# Func 03
def to_tif(
    file: xr.DataArray, path: str, crs: int = 4326, cell_size: Optional[int] = None
):
    """
    Save the generated cube or mosaic to GeoTIFF format

    :param file: xarray.DataArray
    :param path: The path to save the file
    :param crs: The coordinate system to save image
    :param cell_size: The cell size for resampling
    :return: The saved GeoTiff file on the disk
    """
    file = file.squeeze()

    if cell_size is None:
        if crs == 4326:
            raise RuntimeError(f"epsg:4326 cannot be used with cell size")
        else:
            file = file.rio.reproject("epsg:{}".format(crs), resolution=cell_size)

    file = file.where(file != -9999, 0)
    file.rio.set_nodata(input_nodata=0, inplace=True)
    file.rio.to_raster(path, dtype="uint16")
    print("the file was saved!")
