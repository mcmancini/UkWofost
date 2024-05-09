# -*- coding: utf-8 -*-
# Copyright (c) 2024 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), April 2024
# =====================================================
"""
Sample script to build LHS combinations of input parameters to
pass to the WOFOST simulator through file in order to perform checks
of behaviour of Wofost, including diagnostic plotting.
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.dates import DateFormatter
from pandas.plotting import register_matplotlib_converters
from pyproj import Proj, Transformer
from scipy.stats import uniform
from shapely.geometry import Point

register_matplotlib_converters()

NUM_SAMPLES = 100
NUM_VARIABLES = 2

lhs_samples = np.zeros((NUM_SAMPLES, NUM_VARIABLES))

for i in range(NUM_VARIABLES):
    lhs_samples[:, i] = uniform(loc=0, scale=1).ppf(
        np.random.rand(NUM_SAMPLES)
    )

WAV_MIN = 0
WAV_MAX = 60
SMLIM_MIN = 0
SMLIM_MAX = 0.6

lhs_samples[:, 0] = WAV_MIN + lhs_samples[:, 0] * (WAV_MAX - WAV_MIN)
lhs_samples[:, 1] = SMLIM_MIN + lhs_samples[:, 1] * (SMLIM_MAX - SMLIM_MIN)

lhs_dataframe = pd.DataFrame(lhs_samples, columns=["WAV", "SMLIM"])
lhs_dataframe.to_csv(
    (
        "C:/Users/mcm216/OneDrive - University of Exeter/Desktop/"
        "WofostSimulator/lhs_soil.csv"
    ),
    index=False,
)

# Plot runs
WOFOST_SIMULATION_FILE = (
    "C:/Users/mcm216/OneDrive - University of Exeter/"
    "Desktop/WofostSimulator/lonlat_output.csv"
)
output_runs = pd.read_csv(WOFOST_SIMULATION_FILE)

grouped = output_runs.groupby("Rain")
for rain_level, group in grouped:
    fig, ax1 = plt.subplots(figsize=(10, 6))  # Adjust figure size if needed
    ax2 = ax1.twinx()  # Create a secondary y-axis

    ax1.set_title(f"Rain Level {rain_level}")
    ax1.set_xlabel("Day")
    ax1.set_ylabel("Soil moisture")
    ax2.set_ylabel("Yield")

    for iteration in group["iteration"].unique():
        data = group[group["iteration"] == iteration]
        ax1.plot(
            data["day"], data["SM"], label=f"Value 1 - Iteration {iteration}"
        )
        ax2.plot(
            data["day"], data["TWSO"], label=f"Value 2 - Iteration {iteration}"
        )

    ax1.xaxis.set_major_formatter(
        DateFormatter("%Y-%m")
    )  # Adjust date format if needed

    plt.grid(True)
    plt.savefig(
        (
            f"C:/Users/mcm216/OneDrive - University of Exeter/"
            f"Desktop/WofostSimulator/lonlat_{rain_level}_plot.png"
        )
    )
    plt.close()


# Sampling locations
gb_boundary = gpd.read_file(
    "D:/Documents/Data/SEER/____STATE_OF_GB____/SEER_GIS/"
    "Countries (Great Britain)/Countries_December_2016_Full"
    "_Clipped_Boundaries_in_Great_Britain.shp"
)
X_MIN, Y_MIN, X_MAX, Y_MAX = gb_boundary.total_bounds

NUM_SAMPLES = 500
NUM_VARIABLES = 2
lhs_samples = np.zeros((NUM_SAMPLES, NUM_VARIABLES))

for i in range(NUM_VARIABLES):
    lhs_samples[:, i] = uniform(loc=0, scale=1).ppf(
        np.random.rand(NUM_SAMPLES)
    )

lhs_samples[:, 0] = X_MIN + lhs_samples[:, 0] * (X_MAX - X_MIN)
lhs_samples[:, 1] = Y_MIN + lhs_samples[:, 1] * (Y_MAX - Y_MIN)

in_proj = Proj("epsg:27700")
out_proj = Proj("epsg:4326")
transformer = Transformer.from_proj(in_proj, out_proj)

valid_samples = []
for sample in lhs_samples:
    point = Point(sample[0], sample[1])
    # point.set_crs(gb_boundary.crs, inplace=True)
    if gb_boundary.contains(point).any():
        # pylint: disable=E0633
        LAT, LON = transformer.transform(point.x, point.y)
        # pylint: enable=E0633
        valid_samples.append((LON, LAT))

lonlat_df = pd.DataFrame(valid_samples, columns=["lon", "lat"])
duplicated_lonlat = lonlat_df.loc[lonlat_df.index.repeat(2)].reset_index(
    drop=True
)
duplicated_lonlat.to_csv(
    (
        "C:/Users/mcm216/OneDrive - University of Exeter/"
        "Desktop/WofostSimulator/lhs_lonlat.csv"
    ),
    index=False,
)
