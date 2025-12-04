# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), October 2025
# =======================================================
"""
sampler.py
===========
Tools to generate samples of input parameters for WOFOST simulations.
as well as post-process and plot results for diagnostic purposes.
=====================================================================
"""
from datetime import datetime, timedelta
import numpy as np
from pyDOE import lhs
import pandas as pd
from ukwofost.diagnostics.default_ranges import parameter_defaults


class ParameterSampler:
    """Class to handle sampling of input parameters for WOFOST simulations."""

    _default_param_ranges = parameter_defaults
    _TOTAL_N = 625  # Total fertilization amount in kg/ha
    _TOTAL_P = 625  # Total fertilization amount in kg/ha
    _TOTAL_K = 625  # Total fertilization amount in kg/ha

    def __init__(self):
        self.parameter_defaults = self._default_param_ranges

    def sample(self, fixed_params: dict, n_samples: int, sample_params=None):
        """
        n_samples: int, number of samples to generate
        sample_params: list of parameter names to vary
        """
        # Validate parameters passed
        if sample_params is None or sample_params == "all":
            sample_params = [
                p
                for p, v in self.parameter_defaults.items()
                if v[0] is not None
            ]
        self._validate_sampled_parameters(
            sample_params, self.parameter_defaults
        )

        n_sampled = len(sample_params)
        lhs_sample = lhs(n_sampled, samples=n_samples)

        data = {}

        # Fill in sampled parameters using LHS
        for i, param in enumerate(sample_params):
            min_val, max_val = self.parameter_defaults[param][1]
            data[param] = min_val + (max_val - min_val) * lhs_sample[:, i]

        # Fill in remaining parameters with defaults
        remaining_params = set(self.parameter_defaults) - set(sample_params)
        for param in remaining_params:
            default_val = self.parameter_defaults[param][0]
            if default_val is None:
                continue
            data[param] = np.full(n_samples, default_val)

        # Build as DataFrame
        lhs_df = pd.DataFrame(data)

        # Add fixed parameters
        lhs_df = self._add_fixed_parameters(lhs_df, fixed_params)
        lhs_df = self._generate_timing_events(
            lhs_df, fixed_params.get("crop_start_date")
        )
        lhs_df = self._generate_fertilization_amounts(lhs_df, fixed_params)
        return lhs_df

    @staticmethod
    def _validate_sampled_parameters(param_list: list, defaults: dict):
        """Validate that sampled parameters are within the available list."""
        for param in param_list:
            if param not in defaults:
                raise ValueError(f"Parameter {param} not recognized.")

    @staticmethod
    def _add_fixed_parameters(df: pd.DataFrame, fixed_params: dict):
        """Add fixed parameters to each row of the DataFrame."""
        for key, value in fixed_params.items():
            df[key] = value
        return df

    @staticmethod
    def _generate_timing_events(df: pd.DataFrame, crop_start_date: str):
        """
        Generate fertilization timing events for each row in df based on
        crop_start_date.

        Parameters:
            df (pd.DataFrame): DataFrame with n_samples rows
            crop_start_date (str): Crop start date as string "%d/%m/%Y"

        Returns:
            df (pd.DataFrame): DataFrame with added columns N_T1..N_T4
        """
        fmt = "%d/%m/%Y"

        if not isinstance(crop_start_date, str):
            raise TypeError(
                f"crop_start_date must be a string in format {fmt}"
            )

        try:
            start = datetime.strptime(crop_start_date, fmt).date()
        except ValueError as exc:
            msg = (
                f"crop_start_date '{crop_start_date}' "
                f"does not match format {fmt}"
            )
            raise ValueError(msg) from exc

        n_samples = len(df)
        npk_t1 = np.array([start] * n_samples)

        # generate random day offsets for each timing event
        t2_offsets = np.random.randint(1, 183, size=n_samples)
        npk_t2 = np.array(
            [start + timedelta(days=int(offset)) for offset in t2_offsets]
        )

        t3_offsets = np.random.randint(14, 61, size=n_samples)
        npk_t3 = np.array(
            [
                t2 + timedelta(days=int(offset))
                for t2, offset in zip(npk_t2, t3_offsets)
            ]
        )

        t4_offsets = np.random.randint(14, 61, size=n_samples)
        npk_t4 = np.array(
            [
                t3 + timedelta(days=int(offset))
                for t3, offset in zip(npk_t3, t4_offsets)
            ]
        )

        # Format as strings
        df["NPK_T1"] = [d.strftime(fmt) for d in npk_t1]
        df["NPK_T2"] = [d.strftime(fmt) for d in npk_t2]
        df["NPK_T3"] = [d.strftime(fmt) for d in npk_t3]
        df["NPK_T4"] = [d.strftime(fmt) for d in npk_t4]

        return df

    @staticmethod
    def _generate_fertilizer_split(
        df: pd.DataFrame, prefix: str, total_amount: float, fixed_params: dict
    ):
        """
        Generate fertilizer splits for one nutrient (N, P, or K).

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing samples.
        prefix : str
            Nutrient prefix: "N", "P", or "K".
        total_amount : float
            Total applied amount to distribute across 4 timings.
        fixed_params : dict
            Dict of fixed parameters supplied by the user.
        """

        cols = [f"{prefix}_{i}" for i in range(1, 4 + 1)]
        n_samples = len(df)

        # Determine which columns need automatic generation
        to_generate = [col for col in cols if col not in fixed_params]

        # If user fixed all 4: nothing to generate
        if not to_generate:
            return df

        # Generate breakpoints only once (shared for all generated columns)
        break_points = np.random.rand(n_samples, 3)
        break_points.sort(axis=1)

        split_1 = break_points[:, 0] * total_amount
        split_2 = (break_points[:, 1] - break_points[:, 0]) * total_amount
        split_3 = (break_points[:, 2] - break_points[:, 1]) * total_amount
        split_4 = (1 - break_points[:, 2]) * total_amount

        generated = {
            f"{prefix}_1": split_1,
            f"{prefix}_2": split_2,
            f"{prefix}_3": split_3,
            f"{prefix}_4": split_4,
        }

        # Write only columns that are NOT fixed
        for col in to_generate:
            df[col] = generated[col]

        return df

    def _generate_fertilization_amounts(
        self, df: pd.DataFrame, fixed_params: dict
    ):
        """
        Generate fertilizer splits for N, P, and K.
        Only generates values for columns NOT provided in fixed_params.
        """

        df = self._generate_fertilizer_split(
            df, "N", self._TOTAL_N, fixed_params
        )
        df = self._generate_fertilizer_split(
            df, "P", self._TOTAL_P, fixed_params
        )
        df = self._generate_fertilizer_split(
            df, "K", self._TOTAL_K, fixed_params
        )

        return df
