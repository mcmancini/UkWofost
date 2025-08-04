# -*- coding: utf-8 -*-
# Copyright (c) 2025 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), July 2025
# ====================================================
"""
test_api.py
===========
This module contains tests for the API endpoints related to WOFOST simulations.
"""

import pandas as pd
import numpy as np
import requests

df = pd.read_csv(
    "C:/Users/mcm216/OneDrive - University of Exeter/",
    "Desktop/WofostSimulator/wofost-new-rotation_1.csv",
)
df = df.replace({np.nan: None, np.inf: None, -np.inf: None})


# Convert the DataFrame to the expected JSON format
payload = {"runs": df.to_dict(orient="records")}

# URL of your local FastAPI endpoint
url = "http://127.0.0.1:8000/run_bulk"

# Send the POST request
response = requests.post(url, json=payload)
df = pd.DataFrame(response.json()["result"])
