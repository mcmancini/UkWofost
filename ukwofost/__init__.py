# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), December 2023
# ========================================================
"""
UkWofost package initialisation file
"""
import os
from ukwofost.config_parser import AppConfig

current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)
project_root = os.path.abspath(os.path.join(current_directory, ".."))
config_path = project_root + "\\config.ini"
# pylint: disable=E1101
app_config = AppConfig(config_path)
# pylint: enable=E1101
