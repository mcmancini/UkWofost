# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), July 2025
# ====================================================
"""
Models required for API endpoint to run WOFOST simulations.
"""
from typing import List

from pydantic import BaseModel, ConfigDict


class SingleCrop(BaseModel):
    """
    CropRequest model for API endpoint to run WOFOST simulations.
    """

    crop: str
    year: int
    parcel_id: int


class CropRunner(BaseModel):
    """
    CropRunner model for bulk WOFOST simulations.
    """

    parcel_id: int
    crop: str
    year: int
    model_config = ConfigDict(extra="allow")


class BulkRunner(BaseModel):
    """
    BulkRunner model for running multiple WOFOST simulations in bulk.
    """

    runs: List[CropRunner]
