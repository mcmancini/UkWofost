# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), December 2023
# =========================================================
"""
generate_memory.py
==================
This script allows to build and update the memory of crop yields for
any farmer defined in the NetZero+ farm model.

How it works:
Each farmer owns a list of parcels and has an understanding of expected
yields for each crop on the farm based on the knowledge of historic
yields. We define this using the WOFOST crop simulation model run for all
crops and all parcels of the farm of interest for a number of years equal
to the predefined length of the memory of the farmer of interest.
"""
import numpy as np
from tqdm import tqdm
import xarray as xr
from ukwofost.crop_manager import Crop
from ukwofost.crops import Crops
from ukwofost.defaults import defaults
from ukwofost.simulation_manager import WofostSimulator


def get_wofost_yields(sim_start_time, memory_length, parcel_ids):
    """
    Generate memory of historic yields for a farmer
    """
    crops = [crop.value for crop in list(Crops)]
    years = range(sim_start_time - memory_length, sim_start_time)
    np_data = np.empty((len(crops), len(parcel_ids), len(years)))
    coords = {"crop": crops, "parcel": parcel_ids, "year": years}
    dims = ("crop", "parcel", "year")
    yield_data = xr.DataArray(np_data, coords=coords, dims=dims)

    for parcel_id in tqdm(parcel_ids, desc="Processing parcels"):
        sim = WofostSimulator(parcel_id)
        for item in tqdm(Crops, desc="Processing crops", leave=False):
            for year in tqdm(
                range(sim_start_time - memory_length, sim_start_time),
                desc="Processing years",
                leave=False,
            ):
                crop_params = defaults.get("management").get(item.value)
                crop = Crop(year, item.value, **crop_params)
                yield_data.loc[item.value, parcel_ids, year] = sim.run(crop)
    return yield_data


if __name__ == "__main__":
    parcels = ["NT2755072950", "SX8169476504", "ST6922018144", "ST4660232066"]
    START_YEAR = 2030
    YEARS_IN_MEMORY = 5

    memory = get_wofost_yields(
        sim_start_time=START_YEAR,
        memory_length=YEARS_IN_MEMORY,
        parcel_ids=parcels
    )
    memory.to_netcdf("memory.nc")
