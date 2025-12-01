# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), October 2025
# =======================================================
"""
inspector.py
=========
Tools to perform diagnostics, summaries and plotting of WOFOST model simulation
results from a set of sampled input parameters generated with the sampler module
and run with the runner module.
--------------------------------------------------------------------------------
"""

import pandas as pd
import matplotlib.pyplot as plt

class SimulationResults(pd.DataFrame):
    """
    A subclass of pandas.DataFrame for handling and diagnosing WOFOST simulation results.
    """

    # --- Required metadata so pandas operations return your subclass ---
    _metadata = ["model_name"]

    def __init__(self, *args, model_name=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name or "WOFOST_81"

    # Make sure pandas operations preserve the subclass type
    @property
    def _constructor(self):
        return SimulationResults

    def summarize(self) -> pd.DataFrame:
        """
        Summarize the output DataFrame to get final yields for each run.
        
        Returns:
            pd.DataFrame with final yields per run
        """
        if self is None:
            raise ValueError("No output data available. Please run simulations first.")

        # select index of max yield per run
        max_yield_idx = self.groupby("run_id")["yield"].idxmax()

        cols = ["run_id", "day", "yield"]

        # create summary DataFrame
        summary_df = (
            self
            .loc[max_yield_idx, cols]
            .reset_index(drop=True)
        )

        return summary_df

    def plot_summary(self, bins: int = 20):
        """
        Plot a summary of the simulation results.
        """
        if self is None:
            raise ValueError("No output data available. Please run simulations first.")

        summary_df = self.summarize()
        plt.hist(summary_df["yield"], bins=bins, edgecolor="black")
        plt.xlabel("Yield")
        plt.ylabel("Frequency")
        plt.title("Distribution of yield across runs")
        plt.show()
