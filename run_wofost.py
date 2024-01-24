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

from ukwofost.crop_manager import Crop
from ukwofost.defaults import defaults
from ukwofost.simulation_manager import WofostSimulator
from ukwofost.utils import lonlat2osgrid

# Define input parameters
LON, LAT = -3.4111140552800747, 57.13317708272391
CROP = "rapeseed"
YEAR = 2020

# Build Wofost simulator
os_code = lonlat2osgrid((LON, LAT), 10)
sim = WofostSimulator(os_code)

# Define management
crop_params = defaults.get("management").get(CROP)
crop = Crop(YEAR, CROP, **crop_params)

# Run WOFOST to compute crop yield
crop_yield = sim.run(crop)
