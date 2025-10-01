# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), July 2025
# ====================================================
"""
Wofost Yield Simulation API
===========================

This API allows users to run crop yield simulations using the WOFOST model
passing a payload including input parameters such as crop type, year, and
parcel ID. The API will return the simulated yield for the specified input.
"""
from fastapi import FastAPI

from api.endpoints import endpoints

app = FastAPI()
app.include_router(endpoints.router)
