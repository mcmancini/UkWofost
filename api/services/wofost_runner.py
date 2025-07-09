# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), July 2025
# ====================================================
"""
wofost_runner.py
================
"""
import logging

from ukwofost.core.crop_manager import Crop
from ukwofost.core.defaults import defaults
from ukwofost.core.parcel import Parcel
from ukwofost.core.simulation_manager import WofostSimulator

logging.disable(logging.CRITICAL)


def run_crop_simulation(crop: str, year: int, parcel_id: int):
    """Run a WOFOST simulation for a specific crop and year
    at a given parcel.
    """
    parcel = Parcel(parcel_id)
    sim = WofostSimulator(
        location=parcel, weather_provider="Mesoclim", soil_provider="SoilGrids"
    )
    crop_management = defaults.get("management").get(crop)

    if crop_management is None:
        raise ValueError(f"Crop '{crop}' not found in defaults.")

    crop_instance = Crop(calendar_year=year, crop=crop, **crop_management)
    output = sim.run(crop_or_rotation=crop_instance, output_flag="summary")
    return output
