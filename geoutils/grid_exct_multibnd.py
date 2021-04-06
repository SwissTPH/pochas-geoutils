import geopandas as gpd
import pandas as pd
from pathlib import Path
import os
from rasterstats import zonal_stats
import concurrent.futures
from functools import partial


def grid_exct_multibnd(features_path, band_number, stats,img_path):
    """ this func. extract the statistical values for each grid cell
    for from with multi-band image

    Usage: grid_multiband('C:/image/path/exp.tiff',12,'C:/feature/path/exp.geojson',['mean','max'])

    """

    # check whether the image exists or not
    img_dir = Path(img_path)
    ls_s2_img = [file for file in os.listdir(img_dir.parent) if file.endswith(img_dir.name)]


    # Create a list based on the number of the bands
    band_names = list(range(1, band_number + 1))

    # load the features
    path_object = Path(features_path)
    features = gpd.read_file(path_object)

    stats_list = stats

    for i in range(1, band_number + 1):
        for j in range(0, len(stats_list)):
            result = zonal_stats(features.geometry,
                                 img_dir,
                                 band=i,
                                 stats=stats_list[j],
                                 json_out=True)
            features[stats_list[j] + '_band_' + str(band_names[i - 1])] = pd.DataFrame(result)
    return features



def grid_exct_multibnd_parallel(features_path, band_number, stats, img_path_group,max_workers):
    """ this function runs in parallel

    features_path: 'C:/feature/path/exp.geojson'
    band_number: 12
    stats: ['mean','max','std']
    img_path_group: list of the image path

    """
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        a = features_path
        b = band_number
        c = stats
        func = partial(grid_exct_multibnd, a, b, c)
        results = executor.map(func, img_path_group)

        train_data = gpd.read_file(features_path)

        for num, result in enumerate(results):
            for i in range(len(c)):
                for j in range(1, b + 1):
                    train_data = pd.concat((train_data, result[c[i] + '_band_' + str(j)]), axis=1)

    return train_data





