# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), November 2025
# ========================================================
"""
Default parameter ranges for sampling and diagnostics
=====================================================
N.B. The default values are taken for the most part from
the Wofost 8.1 documentation; values for PFFieldCapacity, 
PFWiltingPoint and SurfaceConductivity are taken from 
ChatGPT; these should be reviewed by an expert;
There is a very good chance that the units of SurfaceConductivity
are not cm/second as indicated in the Wofost 8.1 documentation
at https://tinyurl.com/542zk4ca, but rather cm/day.
-----------------------------------------------------------------
"""
parameter_defaults = {
    "SSI": (0.0, [0.0, 100.0], float),
    "SSMAX": (0.0, [0.0, 100.0], float),
    "WAV": (None, [0.0, 6.0], float),
    "CRAIRC": (0.060, [0.04, 0.1], float),
    "SMLIM": (0.6, [0.0, 1.0], float),
    "PFFieldCapacity": (2.0, [1.7, 3.5], float),
    "PFWiltingPoint": (4.2, [2.70, 3.48], float),
    "CO2": (None, [300.0, 1400.0], float),
    "SOPE": (1.47, [1.0, 2.0], float),
    "NAVAILI": (80, [0.0, 250.0], float),
    "PAVAILI": (10, [0.0, 50.0], float),
    "KAVAILI": (20, [0.0, 250.0], float),
    "N_1": (0.0, [0.0, 625.0], float),
    "N_2": (0.0, [0.0, 625.0], float),
    "N_3": (0.0, [0.0, 625.0], float),
    "N_4": (0.0, [0.0, 625.0], float),
    "P_1": (0.0, [0.0, 625.0], float),
    "P_2": (0.0, [0.0, 625.0], float),
    "P_3": (0.0, [0.0, 625.0], float),
    "P_4": (0.0, [0.0, 625.0], float),
    "K_1": (0.0, [0.0, 625.0], float),
    "K_2": (0.0, [0.0, 625.0], float),
    "K_3": (0.0, [0.0, 625.0], float),
    "K_4": (0.0, [0.0, 625.0], float),
}
