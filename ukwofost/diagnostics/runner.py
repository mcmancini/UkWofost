# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), October 2025
# =======================================================
"""
runner.py
=========
Tools to generate model runs and return results for diagnostic purposes
from a set of sampled input parameters generated with the sampler module.
-------------------------------------------------------------------------
"""

import time
import requests
import pandas as pd
from ukwofost.diagnostics.inspector import SimulationResults

class SampleRunner:
    """
    Class to handle running WOFOST simulations for a set of sampled parameters.
    """

    def __init__(self,
                 api_url: str = "http://"
                 "",
                 port: int = 8000,
                 endpoint: str = "run_bulk",
                 summary_flag: str = "full"):
        """
        api_url: str, URL of the FastAPI endpoint to run simulations
        port: int, port number of the API
        endpoint: str, API endpoint for running bulk simulations
        summary_flag: str, type of summary to request ("full", "summary", "harvest")
        """
        self.api_url = f"{api_url}:{port}/{endpoint}?summary={summary_flag}"
        self.input_df = None
        self.output_df = None

    def run(self, samples_df: pd.DataFrame) -> pd.DataFrame:
        """
        Run WOFOST simulations for the provided samples DataFrame.
        
        samples_df: pd.DataFrame, DataFrame containing sampled input parameters
        
        Returns:
            pd.DataFrame with simulation results
        """
        self.input_df = samples_df.copy()
        payload = {"runs": self.input_df.to_dict(orient="records")}

        start = time.time()
        # pylint: disable=W0719, W3101
        response = requests.post(self.api_url, json=payload)
        if response.status_code != 200:
            raise Exception(
                f"API request failed with status code {response.status_code}: "
                f"{response.text}"
            )
        # pylint: enable=W0719, W3101
        end = time.time()
        elapsed_time = end - start
        print(f"Model run completed in {elapsed_time:.2f} seconds")
        results_df = pd.DataFrame(response.json()["result"])
        self.output_df = results_df
        return SimulationResults(results_df, model_name="WOFOST_80")
