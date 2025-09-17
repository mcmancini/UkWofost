# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), December 2023
# ========================================================
"""
UkWofost package initialisation file
"""

import os

from ukwofost.core.config_parser import ConfigReader
from ukwofost.utility.db import create_db_connection
from ukwofost.utility.paths import ROOT_DIR

config_path = os.path.join(ROOT_DIR, "config.ini")
# pylint: disable=E1101
app_config = ConfigReader(config_path)
# pylint: enable=E1101
engine = create_db_connection(app_config)
