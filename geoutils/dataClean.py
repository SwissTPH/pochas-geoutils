# functions to manage the data prepration
from typing import List, Set

import pandas as pd


def rename_column_name(
    df: pd.DataFrame, old_column_list: List[str], new_column_list: List[str]
):
    """
    :param df: Datafrmae which want to change the name of the columns
    :param old_column_list: List of the old columns' name
    :param new_column_list: List of the new columns' name
    :return: change the name of the columns in the datafrme
    """
    df = df.rename(columns=dict(zip(old_column_list, new_column_list)))
    return df


def remove_whitespace(df: pd.DataFrame, skip_rows: str = None):  # type: ignore
    """
    :param df: Datafrrame whcih should be checked for white space
    :param skip_rows: list of the columns which should be ignored
    :return: remove the white space from columns if exists
    """
    if skip_rows == None:
        space = [clm for clm in df.columns if df[clm].dtype == "O"]
    else:
        space = [
            clm for clm in df.columns if df[clm].dtype == "O" and clm not in skip_rows
        ]
    for obj_clm in space:
        df[obj_clm] = df[obj_clm].replace(" ",).astype("float64")
    return df


def transla(name_row: List[str], language_1: List[str], language_2: List[str]):
    """
    :param name_row: The name in row
    :param language_1: List of the first language
    :param language_2: List of the second language
    :return: translated name for each row

    Usage:
    gdf['type_eng'] = gdf['type'].apply(transla,args=(lst_1,lst_2))
    """
    b = [(a[0], a[1]) for a in zip(language_1, language_2)]
    for tup in b:
        if tup[0].lower() == name_row.lower():  # type: ignore
            return tup[1].lower()
