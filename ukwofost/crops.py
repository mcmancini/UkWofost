# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), December 2023
# =========================================================
"""
Generate a class containing crops that can be grown in the UK
"""
from enum import Enum


class Crops(Enum):
    """
    Crops available to grow in the UK
    """

    WHEAT = "wheat"
    POTATO = "potato"
    BARLEY = "barley"
    RAPESEED = "rapeseed"
    GRASS = "grass"
