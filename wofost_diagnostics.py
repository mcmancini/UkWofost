# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), October 2025
# =======================================================
"""
wofost_diagnostics.py
=====================
Script for diagnosing and analyzing WOFOST 8.0 model simulations.
"""

from ukwofost.diagnostics.runner import SampleRunner
from ukwofost.diagnostics.sampler import ParameterSampler

sampler = ParameterSampler()
YEAR = 2022
fixed_params = {
    "crop": "winter_wheat",
    "year": YEAR,
    "parcel_id": 2007797,
    "variety": "Winter_wheat_101",
    "start_crop_calendar": f"01/06/{YEAR}",
    "crop_start_date": f"08/10/{YEAR}",
    "SSI": 0.0,
    "SSMAX": 0.0,
    "WAV": 0.0,
    "CRAIRC": 0.06,
    "SMLIM": 0.6,
    "FIELD_CAPACITY": -0.3,
    "WILTING_POTENTIAL": 3.8,
    "CO2": 400.0,
    "SOPE": 1.47,
    "NAVAILI": 0.0,
    "PAVAILI": 650.0,
    "KAVAILI": 650.0,
    "N_2": 0.0,
    "N_3": 0.0,
    "N_4": 0.0,
    "P_1": 0.0,
    "P_2": 0.0,
    "P_3": 0.0,
    "P_4": 0.0,
    "K_1": 0.0,
    "K_2": 0.0,
    "K_3": 0.0,
    "K_4": 0.0,
}

samples_df = sampler.sample(fixed_params=fixed_params, n_samples=500)

runner = SampleRunner()
results_df = runner.run(samples_df)
# summary_df = runner.summarize()
results_df.summarize()

results_df.plot_summary(bins=30)


# import matplotlib.pyplot as plt
# import pandas as pd

# # --- Select run of interest ---
# run_id = "run1"  # change to whichever run you want

# # 1. Extract the corresponding sample inputs
# sample_row = samples_df.iloc[0]  # first row

# # 2. Extract the corresponding model outputs for that run
# run_df = results_df[results_df["run_id"] == run_id].copy()
# run_df["day"] = pd.to_datetime(run_df["day"])

# # --- Extract fertilization data ---
# N_rates = [
#     sample_row["N_1"],
#     sample_row["N_2"],
#     sample_row["N_3"],
#     sample_row["N_4"],
# ]
# N_dates = [
#     pd.to_datetime(sample_row["N_T1"], format="%d/%m/%Y"),
#     pd.to_datetime(sample_row["N_T2"], format="%d/%m/%Y"),
#     pd.to_datetime(sample_row["N_T3"], format="%d/%m/%Y"),
#     pd.to_datetime(sample_row["N_T4"], format="%d/%m/%Y"),
# ]

# # --- Plotting ---
# fig, ax1 = plt.subplots(figsize=(10, 6))

# # Plot WSO (crop dry weight of storage organ)
# ax1.plot(
#     run_df["day"],
#     run_df["LAI"],
#     color="tab:green",
#     label="LAI (kg/ha)"
# )
# ax1.set_xlabel("Date")
# ax1.set_ylabel("LAI (kg/ha)", color="tab:green")
# ax1.tick_params(axis="y", labelcolor="tab:green")

# # Secondary axis for Ndemand
# ax2 = ax1.twinx()
# ax2.plot(
#     run_df["day"],
#     run_df["NAVAIL"],
#     color="tab:blue",
#     label="N available (kg/ha)",
# )
# ax2.set_ylabel("N Uptake (kg/ha)", color="tab:blue")
# ax2.tick_params(axis="y", labelcolor="tab:blue")

# # Overlay fertilization events
# ax2.scatter(
#     N_dates,
#     N_rates,
#     color="tab:red",
#     s=80,
#     zorder=5,
#     label="Fertilisation (N rate)",
# )
# for i, (date, rate) in enumerate(zip(N_dates, N_rates), 1):
#     ax2.text(
#         date,
#         rate,
#         f"N{i}",
#         color="tab:red",
#         fontsize=9,
#         ha="center",
#         va="bottom",
#     )

# # Titles, legend, formatting
# fig.suptitle(
#     f"Run {run_id}: WSO, N Uptake, and Fertilisation Events", fontsize=14
# )
# fig.autofmt_xdate()

# # Build a combined legend
# lines1, labels1 = ax1.get_legend_handles_labels()
# lines2, labels2 = ax2.get_legend_handles_labels()
# ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

# plt.tight_layout()
# plt.show()
