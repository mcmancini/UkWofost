# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), July 2025
# ====================================================
"""
endpoints.py
===========
This module defines the API endpoints for running crop simulations using
the WOFOST model.
"""

from fastapi import APIRouter, HTTPException

from api.models.crop import BulkRunner, SingleCrop
from api.services.wofost_runner import run_from_payload, run_single_crop

router = APIRouter()


@router.post("/run_crop")
def run_crop(request: SingleCrop):
    """Run a WOFOST simulation for a crop in a specific year and parcel."""
    try:
        result = run_single_crop(request.crop, request.year, request.parcel_id)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/run_bulk")
async def run_bulk(request: BulkRunner, summary: str = "harvest"):
    """Run bulk WOFOST simulations."""
    try:
        result = run_from_payload(request.runs, summary=summary)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
