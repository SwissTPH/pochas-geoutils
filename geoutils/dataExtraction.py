import numpy as np
import numpy.ma as ma
import pandas as pd
import geopandas as gpd
import rasterio as rs


def extract_geotif_to_point(rast_path,gdf_path,resample_size,date='2000',stats='mean',mask=False):
    """
    rast_path: (str, file object or pathlib.Path object)
    gdf_path: (str, file object or pathlib.Path object)
    date: when the raster collected (str): dd_mm_yyyy
    resample_size: The buffer around the points
    stats
    mask
    """
    img = rs.open(rast_path)
    gdf = gpd.read_file(gdf_path)
    rowcol_tuple = img.index(gdf['geometry'].x, gdf['geometry'].y)
    rowcol = np.asarray(rowcol_tuple).T

    pixel_size = img.transform[0]
    size = np.floor((resample_size/pixel_size)/2)

# Define the help function to be used in the main function
    def extract_point(b,rc):
        extracted_values = [b[coord[0], coord[1]] for coord in rc]
        return extracted_values

    def extract_point_buffer(b,rc,s):
        extracted_values = [np.mean(band[coord[0]-s:coord[0] + (s + 1), coord[1]-s:coord[1]+(s+1)]) for coord in rowcol]
        return extracted_values

    def extract_point_buffer_mask(b,rc,s):
        extracted_values = [np.nanmean(ma.masked_values(\
            b[coord[0]-s:coord[0]+(s+1), coord[1]-s:coord[1]+(s+1)], 0).filled(np.nan)) \
                            for coord in rc]
        return extracted_values


    for b in img.indexes:
        band = img.read(b,out_dtype='float32')

        if stats == "mean":
            if size == 0:
                if mask == False:
                    extracted_values = extract_point(band,rowcol)
                    gdf['band_' + str(b) + "_" + date] = extracted_values
                else:
                    raise RuntimeError(f"Extracting point cannot be with mask")
            else:
                if mask == False:
                    extracted_values = extract_point_buffer(band,rowcol,size)
                    gdf['band_'+ str(b) + "_" + date] = extracted_values
                else:
                    extracted_values = extract_point_buffer_mask(band, rowcol, size)
                    gdf['band_' + str(b) + "_" + date] = extracted_values
        else:
            raise NameError(f"Mean only supported")

    return gdf