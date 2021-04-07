# Name: cube.py
# Description: The tools to generate a cube from rasters
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date: 07.14.2021


import xarray as xr
import rioxarray
import pandas as pd

class cube:
    def __init__(self, rast_list, start_date, end_date, freq):
        self.rast_list = rast_list
        self.start_date = start_date
        self.end_date = end_date
        self.freq = freq

    # Func 01
    def generate_cube(self):
        # Concatenate image series
        concat_img = xr.concat(self.rast_list, "time")
        # Add variable name
        concat_img = concat_img.rename('raster')
        # Add timestamp to data
        time = pd.date_range(start=self.start_date, end=self.end_date, freq=self.freq)
        concat_img = concat_img.assign_coords({"time": time})
        return concat_img

    # Func 02
    def generate_mosaic(self,resample_time=None):

        if resample_time==None:
            raise RuntimeError(f"Resample frequency should be determined")

        cub = cube(self.rast_list, self.start_date, self.end_date, self.freq).generate_cube()
        crs = int(cub.attrs['crs'][-4:])
        agg_img = cub.resample(time=resample_time).median()
        agg_img = agg_img.rio.write_crs(crs)
        return agg_img

# Func 03
def to_tif(file,path, crs=4326, cell_size=None):
    file = file.squeeze()
    file = file.rio.write_crs(crs)

    if cell_size!=None:
        if crs==4326:
            raise RuntimeError(f"epsg:4326 cannot be used with cell size")
        else:
            file = file.rio.reproject("epsg:{}".format(crs), resolution=cell_size)

    file = file.where(file != -9999, 0)
    file.rio.set_nodata(input_nodata=0, inplace=True)
    file.rio.to_raster(path, dtype="uint16")
    print('the file was saved!')

