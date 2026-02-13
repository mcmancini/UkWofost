# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), July 2025
# ====================================================
"""
wofost_runner.py
================
"""
import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Literal, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel

from api.core.simulation import run_wofost_simulation
from ukwofost.core.crop_manager import Crop
from ukwofost.core.defaults import defaults
from ukwofost.core.parcel import Parcel
from ukwofost.core.simulation_manager import WofostSimulator
from ukwofost.utility.db import SessionLocal

logging.disable(logging.CRITICAL)


def _worker(run, summary):
    """Worker with its own db session for parallel pooling."""
    session = SessionLocal()
    try:
        return run_wofost_simulation(run, summary, db=session)
    finally:
        session.close()


def run_single_crop(crop: str, year: int, parcel_id: int, db):
    """
    Run a WOFOST simulation for a specific crop and year
    at a given parcel with standard managment.
    """
    parcel = Parcel(parcel_id, db=db)
    sim = WofostSimulator(
        location=parcel, weather_provider="MesoclimParquet", soil_provider="SoilGrids"
    )
    crop_management = defaults.get("management").get(crop)

    if crop_management is None:
        raise ValueError(f"Crop '{crop}' not found in defaults.")

    crop_instance = Crop(calendar_year=year, crop=crop, **crop_management)
    output = sim.run(crop_or_rotation=crop_instance, output_flag="summary")
    return output


def run_from_payload(
    runs: List[Union[dict, BaseModel]],
    summary: Literal["harvest", "full", "summary"],
    db=None,
    parallel: bool = True,
    max_workers: int = os.cpu_count() - 1,
) -> list:
    """
    Runs crop rotations simulations based on a list of parameter dicts.

    Args:
        runs: List of dicts, each dict is a set of input parameters for
        one row.
        parallel: Whether to run in parallel.
        max_workers: Number of worker processes for parallel execution.

    Returns:
        List of dicts with simulation results, JSON-serializable.
    """

    all_results = []
    # Attach an index to every run so we can trace it
    indexed_runs = [(f"run{i+1}", run) for i, run in enumerate(runs)]

    if parallel:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_worker, run, summary): run_id
                for run_id, run in indexed_runs
            }
            for future in as_completed(futures):
                run_id = futures[future]
                df_result = future.result()
                if not df_result.empty:
                    df_result["run_id"] = run_id
                    all_results.append(df_result)
    else:
        for run_id, run in indexed_runs:
            df_result = run_wofost_simulation(run, summary, db=db)
            if not df_result.empty:
                df_result["run_id"] = run_id
                all_results.append(df_result)

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        final_df.replace(
            {np.nan: None, np.inf: None, -np.inf: None}, inplace=True
        )
        return final_df.to_dict(orient="records")
    else:
        return []
