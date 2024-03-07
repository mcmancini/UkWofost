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

import argparse
import math
import pandas as pd
from ukwofost.core.crop_manager import Crop, CropBuilder, CropRotation
from ukwofost.core.defaults import wofost_parameters, moisture_adjustment
from ukwofost.core.simulation_manager import WofostSimulator
from ukwofost.core.utils import lonlat2osgrid, find_contiguous_sets


def apply_conversion(df_row):
    """
    Function to convert yields in kg DM to kg at standard harvest moisture
    """
    try:
        twso = df_row["TWSO"]
        crop = df_row["crop"]

        if isinstance(twso, float) and math.isnan(twso):
            return None

        return twso / (1 - moisture_adjustment.get(crop, 0))
    except TypeError:
        return None


# pylint: disable=R0914
def run_rotations(input_sample_df, output_filename):
    """
    Function that reads the rows of a csv file containing
    input parameters for runs of Wofost, builds crop rotations
    which are then run through Wofost returning a dataframe with
    all WOFOST output parameters
    """
    lonlat = input_sample_df[["lon", "lat"]]
    unique_pairs = lonlat.drop_duplicates(subset=["lon", "lat"])
    crop_yield = pd.DataFrame()
    # Iterate over unique locations
    for _, row in unique_pairs.iterrows():
        lon, lat = row["lon"], row["lat"]
        # initialise simulator
        os_code = lonlat2osgrid((lon, lat), 10)
        sim = WofostSimulator(
            parcel=os_code,
            weather_provider="Chess",
            soil_provider="SoilGrids",
        )
        lonlat_df = input_sample_df[
            (input_sample_df["lon"] == lon) & (input_sample_df["lat"] == lat)
        ]

        # Iterate over rotations
        for rotation in lonlat_df["rotation"].unique():
            rotation_df = lonlat_df[lonlat_df["rotation"] == rotation]
            for item in rotation_df["iteration"].unique():
                try:
                    item_df = rotation_df[rotation_df["iteration"] == item]

                    print(
                        f"Running simulator for '{rotation}' and iteration "
                        f"'{str(item)}' in location '{os_code}'"
                    )
                    # Deal with parameters overridden by user (e.g., initial
                    # soil conditions, or Wofost crop parameters)
                    parameter_dict = item_df.iloc[0, :].to_dict()
                    nonstandard_parameters = {
                        key: value
                        for key, value in parameter_dict.items()
                        if key in wofost_parameters
                    }

                    # Build rotation
                    crops_in_rotation = []
                    for _, row in item_df.iterrows():
                        # Agromanagement of crop rotation
                        crop_args = CropBuilder(row)
                        crop_params = crop_args.crop_parameters
                        crop = Crop(
                            crop_args.calendar_year,
                            crop_args.crop,
                            **crop_params
                        )
                        crops_in_rotation.append(crop)

                    crop_rotation = CropRotation(crops_in_rotation)
                    rotation_output = sim.run(
                        crop_rotation, **nonstandard_parameters
                    ).reset_index(drop=False)

                    rotation_output["lon"], rotation_output["lat"] = lon, lat
                    rotation_output["rotation"] = rotation
                    rotation_output["iteration"] = item
                    crop_list = [
                        list(d.keys())[0] for d in crop_rotation.crop_list
                    ]
                    crop_indices = find_contiguous_sets(rotation_output, "LAI")
                    crop_column = [
                        crop_list[index - 1] if index > 0 else "fallow"
                        for index in crop_indices
                    ]
                    rotation_output["crop"] = crop_column

                    # yield conversion
                    rotation_output["yield"] = rotation_output.apply(
                        apply_conversion, axis=1
                    )

                    crop_yield = pd.concat(
                        [crop_yield, rotation_output], ignore_index=True
                    )

                    print("Done...")
                # pylint: disable=W0621, W0718
                except Exception as e:
                    print(e)
                    continue
                # pylint: enable=W0621, W0718

    crop_yield.to_csv(output_filename, index=False)
    print("All jobs completed\n------------------")


# pylint: disable=R0914

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the Wofost Crop yield simulator"
        )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Path to the input CSV file"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help=(
            "Path of the folder where the output CSV files"
            "will be saved"
        ),
    )

    args = parser.parse_args()
    input_file = args.input
    output_file = args.output
    try:
        input_df = pd.read_csv(input_file)
        run_rotations(input_df, output_file)
    except FileNotFoundError:
        print(f"File not found: {input_file}")
    # pylint: disable=W0718
    except Exception as e:
        print(f"An error occurred: {e}")
    # pylint: disable=W0718
