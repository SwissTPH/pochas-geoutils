# Name: modeling.py
# Description: The tools to prepare the model pipeline with additional functions for visualization
# Author: Behzad Valipour Sh. <behzad.valipour@swisstph.ch>
# Date:28.02.2022


import os
import sys
# Packages
from typing import List

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import pandas as pd
import seaborn as sns
from sklearn.inspection import plot_partial_dependence
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import (GridSearchCV, GroupKFold, KFold,
                                     TimeSeriesSplit, cross_validate,
                                     train_test_split)
from sklearn.preprocessing import FunctionTransformer


def cal_error_metrics(y: npt.ArrayLike, y_pred: npt.ArrayLike):
    """
    Calculation of the error metrics
    
    :param y: True values for dependant variable
    :param y_pred: Predicted values for dependant variable 
    :return: return the the RMSE,MSE,MAE,R2

    """
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    mse = mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    r2 = r2_score(y, y_pred)
    train_test_full_error = pd.DataFrame(
        {"RMSE": [rmse], "MSE": [mse], "MAE": [mae], "R2": r2}
    )
    return train_test_full_error


def scatter_plot(y: npt.ArrayLike, y_pred: npt.ArrayLike, save_path: str = None):
    """
    scatter plot the true vaues and predicted values

    :param y: True values for dependant variable
    :param y_pred: Predicted values for dependant variable
    :param save_path: Path to save the figure
    :return: The scatter plot
    """
    plt.figure(figsize=(8, 8))
    plt.scatter(y, y_pred)
    plt.xlabel("True values")
    plt.ylabel("Predicted values")

    if save_path != None:
        plt.savefig(save_path)


def plot_trend_spatialy(
    y: npt.ArrayLike, y_pred: npt.ArrayLike, xlim: tuple = None, save_path: str = None  # type: ignore
):

    """
    Plot the trend of predicted and true dependant variable. This function consider all the stations to plot

    :param y: True values for dependant variable
    :param y_pred: Predicted values for dependant variable
    :param xlim: Determine the specific interval to focus on
    :param save_path: Path to save the figure
    :return: The trend plot
    """
    plt.figure(figsize=(16, 8))
    plt.plot(y, color="k", alpha=0.3, lw=1, label="True values")
    plt.plot(y_pred, color="b", lw=1, label="Predicted values")
    plt.legend()
    plt.xlabel("Time-Spatial")
    plt.ylabel("Grains/$m^3$")

    if xlim != None:
        plt.xlim(xlim)

    if save_path != None:
        plt.savefig(save_path)


def temperal_cross_validation(
    model,
    X: pd.DataFrame,
    y: pd.Series,
    num_split: int = 5,
    xls_path: str = None,  # type: ignore
    shuffle: bool = True,
):

    """
    Implement temporal cross-validation and calculate the error metrics

    :param model: Trained model
    :param X: predictors
    :param y: dependant variable
    :param num_split: Number of folds
    :param shuffle: Whether to shuffle the data before splitting into batches. Note that the samples within each split will not be shuffled.
    :param xls_path: The path the Excel file should be saved
    :return: calculated the error metrics for each fold with average of them
    """
    cv = KFold(num_split, shuffle=shuffle)
    scores = cross_validate(
        model,
        X,
        y,
        cv=cv,
        scoring=[
            "neg_root_mean_squared_error",
            "neg_mean_squared_error",
            "neg_mean_absolute_error",
            "r2",
        ],
        return_train_score=True,
        n_jobs=-1,
    )

    df_err = pd.DataFrame(scores).T[2:]
    df_err[:6] = df_err[:6] * -1
    df_err.index = [  # type: ignore
        "test_root_mean_squared_error",
        "train_root_mean_squared_error",
        "test_mean_squared_error",
        "train_mean_squared_error",
        "test_mean_absolute_error",
        "train_mean_absolute_error",
        "test_r2",
        "train_r2",
    ]
    df_err.columns = [f"Fold 0{i}" for i in np.arange(1, num_split + 1)]
    df_err.loc[:, "Average_Error"] = df_err.mean(axis=1)

    if xls_path != None:
        df_err.to_excel(xls_path, engine="xlsxwriter")

    return df_err


def plot_temporal_folds(X: pd.DataFrame, num_split: int = 5):
    """
    Plot the temporal cross-validation

    :param X: predictors
    :param num_split: Number of folds
    :return: folds of temperal cross-validation

    """

    fig, ax = plt.subplots(figsize=(10, 5))
    cv = KFold(num_split)
    for ii, (tr, tt) in enumerate(cv.split(X)):
        ax.scatter(tr, [ii] * len(tr), marker="_", s=10, linewidths=40, c="blue")
        ax.scatter(tt, [ii] * len(tt), marker="_", s=10, linewidths=40, c="red")
    plt.show()


def spatial_cross_validation(
    model,
    X: pd.DataFrame,
    y: pd.Series,
    stations: pd.Series,
    num_split=5,
    xls_path=None,
):
    """
    Implement spatial cross-validation and calculate the error metrics

    :param model: Trained model
    :param X: predictors
    :param y: dependant variable
     :param stations: The column which includes the name of the stations
    :param num_split: Number of folds
    :param xls_path: The path the Excel file should be saved
    :return: calculated the error metrics for each fold with average of them
  
    """
    stns = stations.values
    group_kfold = GroupKFold(n_splits=num_split)
    cv = group_kfold.split(X, groups=stns)
    scores = cross_validate(
        model,
        X,
        y,
        cv=cv,
        scoring=[
            "neg_root_mean_squared_error",
            "neg_mean_squared_error",
            "neg_mean_absolute_error",
            "r2",
        ],
        return_train_score=True,
        n_jobs=-1,
    )

    df_err = pd.DataFrame(scores).T[2:]
    df_err[:6] = df_err[:6] * -1
    df_err.index = [  # type: ignore
        "test_root_mean_squared_error",
        "train_root_mean_squared_error",
        "test_mean_squared_error",
        "train_mean_squared_error",
        "test_mean_absolute_error",
        "train_mean_absolute_error",
        "test_r2",
        "train_r2",
    ]

    df_err.columns = [f"Fold 0{i}" for i in np.arange(1, num_split + 1)]
    df_err.loc[:, "Average_Error"] = df_err.mean(axis=1)

    if xls_path != None:
        df_err.to_excel(xls_path, engine="xlsxwriter")

    return df_err


def plot_spatial_cross_validatoion(
    data: pd.DataFrame,
    station_column: str,
    n_splits: int,
    map: str = None,
    title: bool = False,
):
    """
    Plot the Spatial cross-validation

    :param data: Source data include dependant and independent variables
    :param station_column: Column which includes the name of the stations
    :param num_split: Number of folds
    :param map: Path to vector shp or geojson file to plot
    :param title: Should the tile should be plot for the figure or not
    :return: folds of spatial cross-validation

    """

    fig, ax = plt.subplots(
        1, n_splits, figsize=(n_splits * 8, 5), constrained_layout=True
    )

    if map != None:
        ch = gpd.read_file(map)

    stns = data[station_column].values
    group_kfold = GroupKFold(n_splits=n_splits)
    cv = group_kfold.split(data, groups=stns)

    for i, (tr, tt) in enumerate(cv):
        x_tr = data.x.iloc[tr].unique()
        y_tr = data.y.iloc[tr].unique()

        x_tt = data.x.iloc[tt].unique()
        y_tt = data.y.iloc[tt].unique()

        tr_coord = gpd.GeoDataFrame(geometry=gpd.points_from_xy(x_tr, y_tr))  # type: ignore
        tt_coord = gpd.GeoDataFrame(geometry=gpd.points_from_xy(x_tt, y_tt))  # type: ignore

        tr_coord.plot(ax=ax[i - 1], color="Blue", markersize=20, label="Train")  # type: ignore
        tt_coord.plot(ax=ax[i - 1], color="Red", markersize=20, label="Test")
        if map is not None:
            ch.plot(
                ax=ax[i - 1], alpha=1, facecolor="none", edgecolor="black", linewidth=1
            )
        ax[i - 1].legend()
    if title is True:
        fig.suptitle(f"Spatial cross-validation with {n_splits} folds")
    plt.show()


def plot_feature_importances(model, feature_cols: list, save_path: str = None):  # type: ignore
    """"
    Function fetch and plot the importances of the features used during the training process

    :param model: Trained model using sklearn module
    :param feature_cols: Features used during the training process
    :return: The bar plot
    """
    feature_imp = pd.Series(model.feature_importances_, index=feature_cols).sort_values(
        ascending=False
    )
    ax = feature_imp.plot(kind="bar", figsize=(30, 15), fontsize=12)
    ax.set(ylabel="Relative Importance")  # type: ignore
    ax.set(xlabel="Feature")  # type: ignore
    plt.tight_layout()
    if save_path != None:
        plt.savefig(save_path)


def PDP_plot(model, X: pd.DataFrame, feat: list, save_path: str = None):
    """
    Funtion to plot Partial Dependence (PDP)

    :param model: Trained model using sklearn module
    :param X: Features used for training
    :param feat: Features PDP should calculated for
    :return: PDP
    """
    plot_partial_dependence(model, X, feat, n_jobs=-1, grid_resolution=20)
    fig = plt.gcf()
    fig.set_size_inches(16, 16)
    fig.suptitle("Partial dependance of pollen count on first 12 important features")
    fig.subplots_adjust(wspace=0.2, hspace=0.4)
    fig.tight_layout()
    if save_path != None:
        plt.savefig(save_path)


# Feature Engneering
def cos_transformer(period: int):

    """
    cyclical encoding with cosine transformation

    :param period: The numer of the cuclical steps
    :return: Transformend data
    """
    return FunctionTransformer(lambda x: np.cos(x / period * 2 * np.pi))


def sin_transformer(period: int):
    """
    cyclical encoding with sine transformation

    :param period: The numer of the cuclical steps
    :return: Transformend data
    """
    return FunctionTransformer(lambda x: np.sin(x / period * 2 * np.pi))

