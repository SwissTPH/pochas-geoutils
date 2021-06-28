# Name: cube.py
# Description: The tools to generate a cube from rasters
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date: 07.04.2021
# Update: 23.04.2021; 04.05.2021


import xarray as xr
import rioxarray
from rioxarray.merge import merge_arrays
import pandas as pd
from pathlib import Path, PosixPath
import os
from . import utils as ut

def get_imgs(img_list,chunks=(1000,1000)):
    """open the rasters as Dask dataArray"""
    series = [xr.open_rasterio(i,chunks={'x': chunks[0], 'y': chunks[1]}) for i in img_list]
    return series


class cube:
    def __init__(self, rast_list):
        self.rast_list = rast_list

    # Func 01
    def generate_cube(self,start_date,freq):
        # Concatenate image series
        concat_img = xr.concat(self.rast_list, "time")
        # Add variable name
        concat_img = concat_img.rename('raster')
        # Add timestamp to data
        time = pd.date_range(start=start_date, periods=len(self.rast_list), freq=freq)
        concat_img = concat_img.assign_coords({"time": time})
        return concat_img

    # Func 02
    def generate_mosaic(self):
        no_of_bands = max(self.rast_list[0].coords['band'].values)
        crs = int(self.rast_list[0].attrs['crs'][-4:])

        bands_medians = []
        for b in range(no_of_bands):
            bands = [rast.sel(band=b + 1) for rast in self.rast_list]
            bands_comp = xr.concat(bands, dim='band')
            bands_medians.append(bands_comp.median(dim='band', skipna=True))

        bands_medians_cont = xr.concat(bands_medians, dim='band')
        crs_img = bands_medians_cont.rio.write_crs(crs)
        return crs_img


# Func 03
def to_tif(file, path, crs=4326, cell_size=None):
    file = file.squeeze()

    if cell_size is None:
        if crs == 4326:
            raise RuntimeError(f"epsg:4326 cannot be used with cell size")
        else:
            file = file.rio.reproject("epsg:{}".format(crs), resolution=cell_size)

    file = file.where(file != -9999, 0)
    file.rio.set_nodata(input_nodata=0, inplace=True)
    file.rio.to_raster(path, dtype="uint16")
    print('the file was saved!')


# Func 04


def mosaic_from_tiles(in_put_path, out_put_path, dtype="float32", nodata=-9999, mask=None, format="GeoTiff"):
    in_path = Path(in_put_path)
    out_path = Path(out_put_path)

    img_list = ut.list_files_with_absolute_paths(in_path, endswith='.tif')
    if format is "GeoTiff":
        img_list = ut.list_files_with_absolute_paths(in_path, endswith='.tif')
        img_series = [xr.open_rasterio(img) for img in img_list]
    else:
        img_list = ut.list_files_with_absolute_paths(in_path, endswith='.nc')
        img_series = [xr.open_dataarray(img) for img in img_list]

    merged = merge_arrays(img_series)
    if mask is not None:
        merged = merged.where(merged != mask, nodata)

    merged.rio.set_nodata(input_nodata=nodata, inplace=True)
    if format is "GeoTiff":
        merged.rio.to_raster(out_path / 'mosaic_image.tif', dtype=dtype)
    else:
        merged.to_netcdf('mosaic_image.nc', unlimited_dims="time", engine="netcdf4")
    print('Mosaic is created!')
