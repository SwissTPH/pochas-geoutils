# Name: grid.py
# Description: The tools to generate a grid
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date: 14.03.2021

import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point, MultiPoint,box
import pandas as pd


class grid:
    def __init__(self, xmin, xmax, ymin, ymax, cell_size, crs=4326):
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

        self.cell_size = cell_size
        self.crs = crs

    def generate_point(self, center=True):

        """
        The function generate the points based on the bbox received from user
        :return: Points object
        """

        if center == True:
            x = np.arange(np.floor(self.xmin) + self.cell_size / 2, np.floor(self.xmax) - self.cell_size / 2,
                          self.cell_size)
            y = np.arange(np.floor(self.ymin) + self.cell_size / 2, np.floor(self.ymax) - self.cell_size / 2,
                          self.cell_size)
        else:
            x = np.arange(np.floor(self.xmin), np.floor(self.xmax), self.cell_size)
            y = np.arange(np.floor(self.ymin), np.floor(self.ymax), self.cell_size)

        xv, yv = np.meshgrid(x, y)
        df1 = pd.DataFrame({'X': xv.flatten(), 'Y': yv.flatten()})
        df1['coords'] = list(zip(df1['X'], df1['Y']))
        df1['coords'] = df1['coords'].apply(Point)
        gdf1 = gpd.GeoDataFrame(df1, geometry='coords')

        if self.crs != 4326:
            gdf1.set_crs(crs=self.crs, inplace=True)

        return gdf1

    def generate_grid(self):

        """
        The function generate the Grid based on the bbox received from user
        :return: polygon object (Geo-DataFrame)
        """

        df = grid(self.xmin, self.xmax, self.ymin, self.ymax, self.cell_size).generate_point(center=False)
        a = df['coords'].bounds
        lst1 = [a.loc[i] for i in range(a.shape[0])]

        lst2 = [Polygon([(xmin, ymin), (xmin + self.cell_size, ymin), (xmin + self.cell_size, ymin + self.cell_size),
                         (xmin, ymin + self.cell_size)]) for xmin, ymin, xmax, ymax in lst1]

        df = pd.DataFrame(lst2, columns=['geom'])
        gdf = gpd.GeoDataFrame(df, geometry='geom')

        if self.crs != 4326:
            gdf.set_crs(crs=self.crs, inplace=True)
        return gdf

    def cells_within_polygon(self, gdf):
        """
        Generate cells inside the polygons
        :return: The geo-dataframe of cells inside the polygons
        """
        crs = gdf.crs
        grid1 = grid(self.xmin, self.xmax, self.ymin, self.ymax, cell_size=self.cell_size, crs=self.crs).generate_grid()
        grid_intersect = gpd.sjoin(grid1, gdf, op='intersects', how='inner')
        grid_intersect.drop(['index_right', 'id'], axis=1, inplace=True)

        return grid_intersect


# Func 03
def generate_BID(gdf, coords=None, x=None, y=None, circularity=False):
    """
    The function generate ID for each cells in the grid
    :param gdf: Geopandas Data Frame
    :param coords: the name of the coordinate column
    :param x: optional: if the center of the cells are available could be determined with y
    :param y: optional
    :param circularity: Determine roundness of polygon
                    https://gis.stackexchange.com/questions/374053/determine-roundness-of-polygon-in-qgis
    :return: The unique ID for each cell in the grid
    """
    gdf1 = gdf.copy()
    if coords != None:
        gdf1['X'] = gdf1[coords].centroid.x
        gdf1['Y'] = gdf1[coords].centroid.y
        gdf1['BID'] = (np.floor(gdf1['Y'] / 1000) * 100000 + np.floor(gdf1['X'] / 1000)).convert_dtypes()

        if circularity == True:
            gdf1['area'] = gdf1[coords].area
            gdf1['perimeter'] = gdf1[coords].length
            gdf1['circularity_percent'] = (gdf1['area'] * 4 * np.pi) / (gdf1['perimeter'] * gdf1['perimeter']) * 100
            gdf1.drop(['area', 'perimeter'], axis=1, inplace=True)
    elif x != None:
        gdf1['BID'] = (np.floor(gdf1[y] / 1000) * 100000 + np.floor(gdf1[x] / 1000)).convert_dtypes()

        if circularity == True:
            raise RuntimeError(f"it is not polygon")
    else:
        raise RuntimeError(f"Determine the coordinate column")

    return gdf1

