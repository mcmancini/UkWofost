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
import logging

from ukwofost.core.crop_manager import Crop
from ukwofost.core.defaults import defaults
from ukwofost.core.parcel import Parcel
from ukwofost.core.simulation_manager import WofostSimulator

# from ukwofost.core.utils import lonlat2osgrid

logging.disable(logging.CRITICAL)

# Define input parameters
# LON, LAT = -1.670330465465696, 55.028574354445425
CROP = "winter_wheat"
YEAR = 2019
PARCEL_ID = 578422
parcel = Parcel(PARCEL_ID)
# Build Wofost simulator
# os_code = lonlat2osgrid((LON, LAT), 10)
sim = WofostSimulator(
    location=parcel, weather_provider="Mesoclim", soil_provider="SoilGrids"
)

crop_management = defaults.get("management").get(CROP)
crop = Crop(calendar_year=YEAR, crop=CROP, **crop_management)
crop_output = sim.run(crop_or_rotation=crop, output_flag="summary")
# # Define management
# rotation = []
# for item in zip(CROPS, YEARS):
#     crop = item[0]
#     year = item[1]
#     crop_params = defaults.get("management").get(crop)
#     rotation.append(Crop(calendar_year=year, crop=crop, **crop_params))

# crop_rotation = CropRotation(rotation)

# Run WOFOST to compute crop yield
# crop_yield = sim.run(crop_rotation)
# print(crop_yield)
