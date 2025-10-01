# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), July 2025
# ====================================================
"""
simulation.py
=============
Module for core business logic of running individual WOFOST simulations
"""

from typing import Literal

import pandas as pd

from api.utils.utils import apply_conversion
from ukwofost.core.crop_manager import Crop, CropBuilder
from ukwofost.core.defaults import defaults, soil_parameters, wofost_parameters
from ukwofost.core.parcel import Parcel
from ukwofost.core.simulation_manager import WofostSimulator


def run_wofost_simulation(
    run, output_mode: Literal["harvest", "full", "summary"], db=None
):
    """Run an instance of a crop in WOFOST."""
    parcel = run.parcel_id
    try:
        parcel_obj = Parcel(parcel, db=db)
        sim = WofostSimulator(
            location=parcel_obj,
            weather_provider="Mesoclim",
            soil_provider="SoilGrids",
        )

        try:
            parameter_dict = run.model_dump()
        except AttributeError:
            # fallback for pydantic v1 or non-pydantic objects
            try:
                parameter_dict = run.dict()
            except AttributeError:
                # last resort: try to coerce dataclass or object via vars()
                parameter_dict = dict(vars(run))

        nonstandard_parameters = {
            key: value
            for key, value in parameter_dict.items()
            if key in wofost_parameters or key in soil_parameters
        }

        try:
            crop_args = CropBuilder(pd.Series(parameter_dict))
            crop_params = crop_args.crop_parameters
            crop_to_run = Crop(
                crop_args.calendar_year,
                crop_args.crop,
                **crop_params,
            )

        except Exception as e:
            print(f"[WARN] Falling back to default crop parameters: {e}")
            crop_management = defaults.get("management").get(crop_args.crop)
            crop_to_run = Crop(
                crop_args.calendar_year, crop_args.crop, **crop_management
            )
        if output_mode == "summary":
            crop_yield = sim.run(
                crop_or_rotation=crop_to_run,
                output_flag="summary",
                **nonstandard_parameters,
            )
            crop_output = pd.DataFrame(
                [
                    {
                        "parcel_id": parcel,
                        "crop": crop_to_run.crop,
                        "year": crop_to_run.calendar_year,
                        "variety": crop_to_run.variety,
                        "TWSO": crop_yield,
                    }
                ]
            )
            crop_output["yield"] = crop_output.apply(apply_conversion, axis=1)
        else:
            crop_output = sim.run(
                crop_or_rotation=crop_to_run,
                output_flag="full",
                **nonstandard_parameters,
            ).reset_index(drop=False)
            crop_output["crop"] = crop_to_run.crop
            crop_output["parcel_id"] = parcel
            crop_output["year"] = crop_to_run.calendar_year
            crop_output["variety"] = crop_to_run.variety
            crop_output["yield"] = crop_output.apply(apply_conversion, axis=1)
            if output_mode == "harvest":
                max_idx = crop_output["yield"].idxmax()
                crop_output = crop_output.loc[[max_idx]]

        return crop_output

    except Exception as e:
        print(f"Error for parcel {parcel}: {e}")
        return pd.DataFrame()
