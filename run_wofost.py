# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), January 2024
# =======================================================
"""
run_wofost.py
=============
Run an instance of WOFOST for any location in the UK, for any
user-defined crop and agromanagement.
This will be the main script for testing WOFOST, compare
versions, build features and so on.

INPUT PARAMETERS
:param LON, LAT: coordinates of the location for which Wofost
        needs to be run
:param CROP: crop of interest
:param YEAR: year of interest

Crop details and agromanagment are loaded from a file containing
default values for the specific crop. They can be overwritten
to have user-sepcified values. This can be done in the section
called "Define management", line 43 and following. The best option
is to load the default crop parameters (line 44) and change their
values before passing the crop_params dictionary when the instance
of the Crop class is instantiated (line 45). More information on
agromanagment can be found at https://tinyurl.com/bdcmj5b7
"""
import copy
import logging
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt

from ukwofost.core.crop_manager import Crop, CropRotation
from ukwofost.core.defaults import defaults
from ukwofost.core.parcel import Parcel
from ukwofost.core.simulation_manager import WofostSimulator

# from ukwofost.core.utils import lonlat2osgrid

logging.disable(logging.CRITICAL)

# Define input parameters
# LON, LAT = -1.670330465465696, 55.028574354445425
CROP = "winter_wheat"
YEAR = 2019
PARCEL_ID = 1491
parcel = Parcel(PARCEL_ID)
# Build Wofost simulator
# os_code = lonlat2osgrid((LON, LAT), 10)
sim = WofostSimulator(
    location=parcel, weather_provider="Mesoclim", soil_provider="SoilGrids"
)

crop_management = copy.deepcopy(defaults.get("management").get(CROP))
crop_management["start_crop_calendar"] = dt.date(YEAR, 6, 1)
crop_management["crop_start_date"] = dt.date(YEAR, 10, 8)
crop_1 = Crop(calendar_year=YEAR, crop=CROP, **crop_management)

crop_management_2 = copy.deepcopy(defaults.get("management").get(CROP))
crop_management_2["crop_start_date"] = dt.date(YEAR + 1, 10, 8)
crop_2 = Crop(calendar_year=YEAR, crop=CROP, **crop_management_2)


rotation = CropRotation([crop_1, crop_2])
kwargs = {
    "WAV": 2,
    "SMLIM": 0.50,
}
crop_output = sim.run(crop_or_rotation=rotation, output_flag="full", **kwargs)

weather = pd.DataFrame(sim.wdp.export()).set_index("DAY")
weather = weather[["IRRAD", "TMIN", "TMAX", "VAP", "RAIN", "WIND"]]
output = crop_output[
    ["SM", "WWLOW", "RD", "NAVAIL", "PAVAIL", "KAVAIL", "TWSO"]
]
output = pd.merge(
    weather, output, left_index=True, right_index=True, how="inner"
)

save_folder = "Z:/PCSE-WOFOST/Wofost_tests/"
savename = "run_13_WAV2_SMLIM050_rotation"
output.to_csv(f"{save_folder}{savename}.csv")

ax = output["SM"].plot(
    figsize=(10, 6), label="Soil Moisture (SM)", color="tab:blue"
)
output["RAIN"].plot(
    ax=ax, secondary_y=True, label="Rainfall (RAIN)", color="tab:gray"
)
ax.set_ylabel("Soil Moisture")
ax.right_ax.set_ylabel("Rainfall (mm)")
ax.set_xlabel("Date")

# Combine legends from both axes
lines, labels = ax.get_legend_handles_labels()
lines2, labels2 = ax.right_ax.get_legend_handles_labels()
ax.legend(lines + lines2, labels + labels2, loc="upper right")

plt.title("Soil Moisture and Rainfall Over Time")
plt.tight_layout()
plt.savefig(f"{save_folder}{savename}.png", dpi=300, bbox_inches="tight")
plt.show()
