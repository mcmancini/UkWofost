# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), January 2024
# =======================================================
"""
This file contains paths relative to the project root that can be imported.
Please note that if this file moves relative to the project root,
find_repo_root() must be changed.
"""

import os


def find_project_root():
    """
    Returns
    -------
    Str:
        Root folder for the project. Current file is assumed to be at:
        "NetZero/netzero/utility/paths.py".
    """

    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


ROOT_DIR = find_project_root()
RESOURCES_DIR = os.path.join(ROOT_DIR, "resources")
PARCEL_DATA_DIR = os.path.join(RESOURCES_DIR, "land_parcels")
PARCEL_DATA = os.path.join(PARCEL_DATA_DIR, "land_parcels.shp")
