# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), July 2025
# ====================================================
"""
utils.py
===========
Utility module for the API
"""

import math

from ukwofost.core.defaults import moisture_adjustment


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
