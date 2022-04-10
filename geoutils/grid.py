# Name: grid.py
# Description: The tools to generate a grid
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date: 14.03.2021

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiPoint, Point, Polygon, box

gpd.GeoDataFrame


class grid:
    def __init__(
        self,
        xmin: float,
        xmax: float,
        ymin: float,
        ymax: float,
        cell_size: float,
        crs: int = 4326,
    ):
        """
        Generate a reqular grid or point

        :param xmin: The left-low corner X coordinate
        :param xmax: The right-up corner X coordinate
        :param ymin: The left-low corner Y coordinate
        :param ymax: The right-up corner Y coordinate
        """
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

        self.cell_size = cell_size
        self.crs = crs

    def generate_point(self, center: bool = True) -> gpd.GeoDataFrame:

        """
        The function generate the points based on the bbox received from user
        
        :param center: whether to generate point for center of the grid or not
        :return: gpd.GeoDataFrame
        """

        if center == True:
            x = np.arange(
                np.floor(self.xmin) + self.cell_size / 2,
                np.floor(self.xmax) - self.cell_size / 2,
                self.cell_size,
            )
            y = np.arange(
                np.floor(self.ymin) + self.cell_size / 2,
                np.floor(self.ymax) - self.cell_size / 2,
                self.cell_size,
            )
        else:
            x = np.arange(np.floor(self.xmin), np.floor(self.xmax), self.cell_size)
            y = np.arange(np.floor(self.ymin), np.floor(self.ymax), self.cell_size)

        xv, yv = np.meshgrid(x, y)
        df1 = pd.DataFrame({"X": xv.flatten(), "Y": yv.flatten()})
        df1["coords"] = list(zip(df1["X"], df1["Y"]))
        df1["coords"] = df1["coords"].apply(Point)
        gdf1 = gpd.GeoDataFrame(df1, geometry="coords")  # type: ignore

        if self.crs != 4326:
            gdf1.set_crs(crs=self.crs, inplace=True)

        return gdf1

    def generate_grid(self) -> gpd.GeoDataFrame:

        """
        The function generate the Grid based on the bbox received from user

        :return: -> gpd.GeoDataFrame
        """

        df = grid(
            self.xmin, self.xmax, self.ymin, self.ymax, self.cell_size
        ).generate_point(center=True)["coords"]
        cell_cds = np.vstack([df.x, df.y]).T
        cs = np.apply_along_axis(
            lambda x: box(
                x[0] - self.cell_size / 2,
                x[1] - self.cell_size / 2,
                x[0] + self.cell_size / 2,
                x[1] + self.cell_size / 2,
            ),
            1,
            cell_cds,
        )

        gdf = gpd.GeoDataFrame(cs, columns=["geom"], crs=self.crs, geometry="geom")  # type: ignore

        return gdf

    def cells_within_polygon(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Generate cells inside the polygons

        :return: The geo-dataframe of cells inside the polygons
        """
        crs = gdf.crs
        grid1 = grid(
            self.xmin,
            self.xmax,
            self.ymin,
            self.ymax,
            cell_size=self.cell_size,
            crs=self.crs,
        ).generate_grid()
        grid_intersect = gpd.sjoin(grid1, gdf, op="intersects", how="inner")
        grid_intersect.drop(["index_right", "id"], axis=1, inplace=True)

        return grid_intersect


# Func 03
def generate_BID(
    gdf: gpd.GeoDataFrame,
    coords: str = None,  # type: ignore
    cell: int = None,  # type: ignore
    x: float = None,  # type: ignore
    y: float = None,  # type: ignore
    circularity: bool = False,
):
    """
    The function generate ID for each cells in the grid

    :param gdf: Geopandas Data Frame
    :param coords: the name of the coordinate column
    :param x: optional: if the center of the cells are available could be determined with y
    :param y: optional
    :param circularity: Determine roundness of polygon https://gis.stackexchange.com/questions/374053/determine-roundness-of-polygon-in-qgis
    :return: The unique ID for each cell in the grid
    """
    gdf1 = gdf.copy()
    if coords != None:
        if cell == None:
            raise RuntimeError(f"Determine the cell size")
        else:
            gdf1["X"] = gdf1[coords].centroid.x
            gdf1["Y"] = gdf1[coords].centroid.y
            gdf1["BID"] = (
                np.floor(gdf1["Y"] / cell) * 100000 + np.floor(gdf1["X"] / cell)
            ).convert_dtypes()

        if circularity == True:
            gdf1["area"] = gdf1[coords].area
            gdf1["perimeter"] = gdf1[coords].length
            gdf1["circularity_percent"] = (
                (gdf1["area"] * 4 * np.pi)
                / (gdf1["perimeter"] * gdf1["perimeter"])
                * 100
            )
            gdf1.drop(["area", "perimeter"], axis=1, inplace=True)
    elif x != None:
        gdf1["BID"] = (
            np.floor(gdf1[y] / 1000) * 100000 + np.floor(gdf1[x] / 1000)
        ).convert_dtypes()

        if circularity == True:
            raise RuntimeError(f"it is not polygon")
    else:
        raise RuntimeError(f"Determine the coordinate column")

    return gdf1

