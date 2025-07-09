# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), July 2025
# ====================================================
"""
enpoints.py
===========
This module defines the API endpoints for running crop simulations using
the WOFOST model.
"""

from fastapi import APIRouter, HTTPException

from api.models.crop import CropRequest
from api.services.wofost_runner import run_crop_simulation

router = APIRouter()


@router.post("/run_crop")
def run_crop(request: CropRequest):
    """Run a WOFOST simulation for a crop in a specific year and parcel."""
    try:
        result = run_crop_simulation(
            request.crop, request.year, request.parcel_id
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
