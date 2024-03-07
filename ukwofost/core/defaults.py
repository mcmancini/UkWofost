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

from ukwofost.core import app_config
from ukwofost.core.config_parser import ConfigReader

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

wofost_parameters = set(
    [
        "AMAXTB",
        "BG_K_SUPPLY",
        "BG_N_SUPPLY",
        "BG_P_SUPPLY",
        "CFET",
        "CO2",
        "CO2AMAXTB",
        "CO2EFFTB",
        "CO2TRATB",
        "CONTAB",
        "CRAIRC",
        "CVL",
        "CVO",
        "CVR",
        "CVS",
        "DEFLIM",
        "DEPNR",
        "DLC",
        "DLO",
        "DTSMTB",
        "DVSEND",
        "DVSI",
        "DVS_NPK_STOP",
        "DVS_NPK_TRANSL",
        "EFFTB",
        "FLTB",
        "FOTB",
        "FRTB",
        "FSTB",
        "IAIRDU",
        "IDSL",
        "IFUNRN",
        "IOX",
        "K0",
        "KAVAILI",
        "KCRIT_FR",
        "KDIFTB",
        "KMAXLV_TB",
        "KMAXRT_FR",
        "KMAXSO",
        "KMAXST_FR",
        "KRESIDLV",
        "KRESIDRT",
        "KRESIDST",
        "KSOILBASE",
        "KSOILBASE_FR",
        "KSUB",
        "NAVAILI",
        "NCRIT_FR",
        "NFIX_FR",
        "NLAI_NPK",
        "NLUE_NPK",
        "NMAXLV_TB",
        "NMAXRT_FR",
        "NMAXSO",
        "NMAXST_FR",
        "NOTINF",
        "NPART",
        "NPK_TRANSLRT_FR",
        "NRESIDLV",
        "NRESIDRT",
        "NRESIDST",
        "NSLA_NPK",
        "NSOILBASE",
        "NSOILBASE_FR",
        "PAVAILI",
        "PCRIT_FR",
        "PERDL",
        "PMAXLV_TB",
        "PMAXRT_FR",
        "PMAXSO",
        "PMAXST_FR",
        "PRESIDLV",
        "PRESIDRT",
        "PRESIDST",
        "PSOILBASE",
        "PSOILBASE_FR",
        "Q10",
        "RDI",
        "RDMCR",
        "RDMSOL",
        "RDRLV_NPK",
        "RDRRTB",
        "RDRSTB",
        "RFSETB",
        "RGRLAI",
        "RKUPTAKEMAX",
        "RML",
        "RMO",
        "RMR",
        "RMS",
        "RNUPTAKEMAX",
        "RPUPTAKEMAX",
        "RRI",
        "SLATB",
        "SM0",
        "SMFCF",
        "SMLIM",
        "SMTAB",
        "SMW",
        "SOLNAM",
        "SOPE",
        "SPA",
        "SPADS",
        "SPAN",
        "SPASS",
        "SPODS",
        "SPOSS",
        "SSATB",
        "SSI",
        "SSMAX",
        "TBASE",
        "TBASEM",
        "TCKT",
        "TCNT",
        "TCPT",
        "TDWI",
        "TEFFMX",
        "TMNFTB",
        "TMPFTB",
        "TSUM1",
        "TSUM2",
        "TSUMEM",
        "VERNBASE",
        "VERNDVS",
        "VERNRTB",
        "VERNSAT",
        "WAV",
    ]
)

moisture_adjustment = {
    "wheat": 0.145,
    "barley": 0.145,
    "rapeseed": 0.9,
    "potato": 0.79,
    "rye_grass": 0.75,
    "maize": 0.155,
    "fallow": None,
}
