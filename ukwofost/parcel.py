# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), January 2024
# =======================================================
"""
parcel.py
---------

Generate parcels with attributed to be used to instantiate
WofostSimulator objects.
"""

import warnings
import geopandas as gpd
from ukwofost.utils import lonlat2osgrid


class Parcel:
    """
    Class Parcel
    ------------
    An instance of this class is a "Parcel" object which
    contains all the data required to build an instance of the
    WofostSimulator class in order to compute crop yields.

    Parameters for initialisation
    -----------------------------
    :param gid (Int): the ID of the parcel. This must be an ID
        in the list of parcel IDs contained in the CEH UK Land Cover
        Map in vector format. These IDs are required in order to identify
        the correct weather and soil data associated with the parcel, which
        will then passed to the WofostSimulator.

    Methods defined here:
    ---------------------

    __str__(self, /)
        Return str(self).
    """

    def __init__(self, gid):
        self._parcel_id = gid

    @property
    def parcel_id(self):
        """Set parcel ID"""
        return self._parcel_id

    @property
    def osgrid_code(self):
        """Set OS grid reference code of parcel centroid"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return self.calc_os_code(self.parcel_id)

    @staticmethod
    def calc_os_code(parcel_id):
        """
        Compute OS grid code of the centroid
        of the parcel with id = "parcel_id"
        """
        parcels_shapefile = gpd.read_file("./resources/land_parcels/land_parcels.shp")
        parcel_centroid = parcels_shapefile[
            parcels_shapefile["gid"] == str(parcel_id)
        ].centroid
        lon_lat = (parcel_centroid.x, parcel_centroid.y)
        os_code = lonlat2osgrid(coords=lon_lat, figs=8)
        return os_code

    def __str__(self):
        msg = "======================================================\n"
        msg += "               Parcel characteristics\n"
        msg += "---------------------Description----------------------\n"
        msg += f"Parcel ID: {str(self.parcel_id)}\n"
        msg += f"Parcel OS Grid code: {self.osgrid_code}"
        return msg
