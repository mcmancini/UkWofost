# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), December 2023
# ========================================================
"""
Default settings for running WOFOST for any longitude-
latitude pair in the UK
"""

from pcse.fileinput import YAMLCropDataProvider
from pcse.util import WOFOST80SiteDataProvider
from ukwofost import app_config
from ukwofost.config_parser import ConfigReader

# CLIMATE
RCP = "rcp26"
ENSEMBLE = 1
SOILSOURCE = "SoilGrids"

# CROP PARAMETERS
# pylint: disable=E1101
cropd = YAMLCropDataProvider(app_config.data_dirs["crop_dir"], force_reload=True)

# SITE PARAMETERS
sitedata = WOFOST80SiteDataProvider(
    WAV=100,
    CO2=360,
    NAVAILI=80,
    PAVAILI=10,
    KAVAILI=20,
)

sitedata["TemperatureSoilinit"] = 5.0


"""
CROP AGROMANAGEMENT ARGS
========================

These are agromanagement events such as sowing and fertilisation.
They are contained in a yaml file with default variables for each
crop. These can be overwritten to adapt agromanagement to the user's
needs
"""
management_dir = app_config.data_dirs["management_dir"]
management = ConfigReader(management_dir + "crop_management.yaml")
# pylint: enable=E1101

defaults = {
    "rcp": RCP,
    "ensemble": ENSEMBLE,
    "soilsource": SOILSOURCE,
    "cropd": cropd,
    "sitedata": sitedata,
    "management": management,
}
