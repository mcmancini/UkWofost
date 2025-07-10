# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), July 2025
# ====================================================
"""
Models required for API endpoint to run WOFOST simulations.
"""
from pydantic import BaseModel


class CropRequest(BaseModel):
    """
    CropRequest model for API endpoint to run WOFOST simulations.
    """

    crop: str
    year: int
    parcel_id: int
