# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), January 2024
# =======================================================
"""
parcel.py
---------

Generate parcels with attributes to be used to instantiate
WofostSimulator objects.
"""

import warnings
import geopandas as gpd
from ukwofost.core import app_config
from ukwofost.core.utils import lonlat2osgrid, get_dtm_values
from ukwofost.utility.paths import PARCEL_DATA


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
            return self._calc_spatial_attributes()["osgrid_code"]

    @property
    def lon(self):
        """Assign longitude of parcel centroid"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return self._calc_spatial_attributes()["lon"]

    @property
    def lat(self):
        """Assign latitude of parcel centroid"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return self._calc_spatial_attributes()["lat"]

    @property
    def elevation(self):
        """Set parcel elevation if exists"""
        return self._calc_elevation(self.osgrid_code)

    @staticmethod
    def _calc_elevation(os_code):
        """Retrieve elevation of the centroid of the parcel"""
        try:
            elevation = round(get_dtm_values(os_code, app_config)["elevation"])
        except ConnectionError:
            elevation = 0
        return elevation

    def _calc_spatial_attributes(self):
        """
        Compute OS grid code of the centroid
        of the parcel with id = "parcel_id"
        """
        parcels_shapefile = gpd.read_file(PARCEL_DATA)
        parcel_centroid = parcels_shapefile[
            parcels_shapefile["gid"] == str(self.parcel_id)
        ].centroid
        lon, lat = (parcel_centroid.iloc[0].x, parcel_centroid.iloc[0].y)
        osgrid_code = lonlat2osgrid(coords=(lon, lat), figs=8)
        return {
            "osgrid_code": osgrid_code,
            "lon": lon,
            "lat": lat,
        }

    def __str__(self):
        msg = "======================================================\n"
        msg += "               Parcel characteristics\n"
        msg += "---------------------Description----------------------\n"
        msg += f"Parcel ID: {str(self.parcel_id)}\n"
        msg += f"Parcel OS Grid code: {self.osgrid_code}\n"
        msg += f"Parcel elevation: {self.elevation} metres\n"
        return msg
