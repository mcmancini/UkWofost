# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), January 2024
# =======================================================
"""
bulk_wofost_simulator.py
========================
Run multiple instances of WOFOST based on an input file
(a .csv file) containing in each row a combination of
input parameters within the full input parameter space
allowed by WOFOST. Briefly, there can be categorized into:
    - 1) Initial soil conditions
    - 2) agromanagement (crops, varieties, rotations)
    - 3) location (hence weather and soil)
    - 4) year (hence also weather)
While not needed at the moment, this script will allow to
also override default crop parameters
Given the structure of the WofostSimulator, we first set
appropriate initial parameters for each crop using instances
of the Crop class, and then we build rotations (which are
going to be identifiable in the .csv file as multiple rows
which correspond to the same rotation identifier) using
instances of the CropRotation class
"""

import pandas as pd
from ukwofost.crop_manager import Crop, CropBuilder
from ukwofost.simulation_manager import WofostSimulator
from ukwofost.utils import lonlat2osgrid

# Load csv sample file
sample_runs = pd.read_csv("resources/Wofost_test.csv")

sample = sample_runs.iloc[0, :]

crop_args = CropBuilder(sample)
crop_params = crop_args.crop_parameters
crop = Crop(crop_args.calendar_year, crop_args.crop, **crop_params)

LON, LAT = -3.4111140552800747, 57.13317708272391
os_code = lonlat2osgrid((LON, LAT), 10)
sim = WofostSimulator(os_code)

crop_yield = sim.run(crop)
