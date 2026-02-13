# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), January 2024
# =======================================================
"""
run_wofost_parallel.py
======================
Test script based on ./run_wofost.py to run multiple instances of WOFOST
in parallel using the multiprocessing library.

INPUT PARAMETERS

:param CROP: crop of interest
:param YEAR: year of interest
:param PARCEL_ID: ID of the parcel to be used for the simulation. This is
    CEH LCM parcel IDs

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
import multiprocessing

from ukwofost.core.crop_manager import Crop
from ukwofost.core.defaults import defaults
from ukwofost.core.parcel import Parcel
from ukwofost.core.simulation_manager import WofostSimulator

logging.disable(logging.CRITICAL)

# Input parameters
CROP = "winter_wheat"
YEAR = 2019
PARCEL_ID = 578422

# Create reusable data
crop_management = defaults.get("management").get(CROP)


# Function to run one simulation
def run_single_simulation(sim_index):
    """wrapper function to run a single wofost simulation"""
    parcel = Parcel(PARCEL_ID)
    sim = WofostSimulator(
        location=parcel, weather_provider="MesoclimParquet", soil_provider="SoilGrids"
    )
    crop = Crop(calendar_year=YEAR, crop=CROP, **crop_management)
    result = sim.run(crop_or_rotation=crop, output_flag="summary")
    print(f"Simulation {sim_index} completed.")
    return result


if __name__ == "__main__":
    NUM_SIMULATIONS = 10

    with multiprocessing.Pool(processes=NUM_SIMULATIONS) as pool:
        results = pool.map(run_single_simulation, range(NUM_SIMULATIONS))

    for i, output in enumerate(results):
        print(f"Sim {i}: Final TWSO = {output}")
