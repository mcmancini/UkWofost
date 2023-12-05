# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), October 2023
# =======================================================
"""
soil_manager.py
===============

Script containing the soil data provider classes to import and preprocess
the soil data reqiured to run Wofost.
It contains the following:
- class SoilDataProvider: parent class for all soil data providers.
- class SoilGridsDataProvider: child class that deals with soil data from
  the SoilGrids soil data source (https://www.isric.org/explore/soilgrids)
- class WHSDDataProvider: child class that deals with soil data from
  the FAO World Harmonized Soil Database (https://tinyurl.com/y3b83h53)
Any other soil data source will have its own child class defined here
"""
from math import log10
import numpy as np
from rosetta import rosetta, SoilData
from soiltexture import getTexture
import xarray as xr
from ukwofost import app_config
from ukwofost.utils import osgrid2lonlat, water_retention, water_conductivity, nearest


class SoilDataProvider(dict):
    """
    Base class for all soil data providers
    """

    # class attributes
    _DATA_SOURCE = None
    _DEFAULT_SOILVARS = ["sand", "silt", "clay"]
    _WILTING_POTENTIAL = log10(1.5e4)
    _FIELD_CAPACITY = log10(150)

    _defaults = {
        "CRAIRC": 0.060,
        "SOPE": 1.47,
        "KSUB": 1.47,
        "RDMSOL": 80,
        "SPADS": 0.100,
        "SPODS": 0.030,
        "SPASS": 0.200,
        "SPOSS": 0.050,
        "DEFLIM": -0.300,
    }

    def __init__(self):
        dict.__init__(self)
        self.update(self._defaults)

    def _return_soildata(self, osgrid_code, soil_texture_list):
        # pylint: disable=R0914
        lon, lat = osgrid2lonlat(osgrid_code, epsg=4326)
        rosettasoil = SoilData.from_array([soil_texture_list])
        mean, *_ = rosetta(3, rosettasoil)  # int=rosetta version
        theta_r = mean[0][0]
        theta_s = mean[0][1]
        alpha = 10 ** mean[0][2]
        npar = 10 ** mean[0][3]
        k_0 = 10 ** mean[0][4]
        psi = list(np.arange(0, 6.1, 0.1).tolist())
        psi = [-1] + psi  # saturation
        water_ret = [water_retention(x, theta_r, theta_s, alpha, npar) for x in psi]
        water_cond = [
            water_conductivity(x, theta_r, theta_s, alpha, npar, k_0) for x in psi
        ]
        smtab = [x for pair in zip(psi, water_ret) for x in pair]
        # Permanent wilting point conventianally at 1500 kPa, fc between 10-30kPa
        wp_idx = psi.index(nearest(self._WILTING_POTENTIAL, psi))
        fc_idx = psi.index(nearest(self._FIELD_CAPACITY, psi))
        smw = water_ret[wp_idx]
        smfcf = water_ret[fc_idx]
        sm0 = water_ret[0]
        contab = [x for pair in zip(psi, water_cond) for x in pair]
        # Provide soil texture given percentage of sand and clay
        solnam = getTexture(
            soil_texture_list[0], soil_texture_list[2], classification="INTERNATIONAL"
        )

        return {
            "osgrid_code": osgrid_code,
            "lon": lon,
            "lat": lat,
            "SOLNAM": solnam,
            "SMTAB": smtab,
            "SMW": smw,
            "SMFCF": smfcf,
            "SM0": sm0,
            "CONTAB": contab,
            "K0": k_0,
        }
        # pylint: enable=R0914

    def __str__(self):
        msg = "============================================\n"
        msg += f"Soil data provided by: {self.__class__.__name__}\n"
        msg += "----------------Description-----------------\n"
        msg += f"Soil data for parcel in OS cell {self['osgrid_code']} \n"
        msg += f"Lon: {self['lon']:.3f}; Lat: {self['lat']:.3f}\n"
        msg += f"Data Source: {self._DATA_SOURCE}\n"
        msg += "============================================\n\n"
        for key, value in self.items():
            if isinstance(value, list):
                # only print first 20 elements of list
                rounded_list = [round(x, 2) for x in value[0:20]]
                msg += f"{key}: {rounded_list} {type(value)}\n"
            else:
                msg += f"{key}: {value} {type(value)}\n"
        return msg


class SoilGridsDataProvider(SoilDataProvider):
    """
    Read soil data from netcdf file. This data provider is set to
    work with the SoilGrids data retrieved using the script
    'bulk_SoilGrids_downloader.py'.

    Input arguments
    :param osgrid_code: the OS Grid Code of the parcel for which soil
           soil data is required.

    Methods defined here:

    _load_soil_data(self, osgrid_code)
        Return a list of %sand, %silt, %clay for the soil in the
        location specified by osgrid_code

    """

    # pylint: disable=E1101
    _SOIL_PATH = app_config.data_dirs["soil_dir"] + "GB_soil_data.nc"
    _DATA_SOURCE = "SoilGrids\nhttps://www.isric.org/explore/soilgrids"
    # pylint: enable=E1101

    def __init__(self, osgrid_code):
        super().__init__()
        soil_texture_list = self._load_soil_data(osgrid_code)
        self.update(self._return_soildata(osgrid_code, soil_texture_list))

    def _load_soil_data(self, osgrid_code):
        """
        Retrieve soil data from xarray file based on location defined in
        osgrid_code
        """
        lon, lat = osgrid2lonlat(osgrid_code, epsg=4326)
        soil_array = xr.open_dataset(SoilGridsDataProvider._SOIL_PATH)
        soil_df = (
            soil_array.sel(x=lon, y=lat, method="nearest")
            .to_dataframe()
            .reset_index()[self._DEFAULT_SOILVARS]
        )
        # rosetta requires [%sand, %silt, %clay, bulk density, th33, th1500]
        # in this order. Last 3 optional
        soil_df = soil_df.iloc[0].tolist()
        return soil_df


# class WHSDDataProvider(SoilDataProvider):
#     """
#     Read soil data from the WHSD. This data is currently stored after
#     processing in a postgreSQL database at a 2km spatial resolution
#     (NEV SEER grid.)

#     INPUT DATA
#     :param osgrid_code: the OS Grid Code of the parcel for which soil
#            soil data is required.
#     """

#     # class attributes
#     _DATA_SOURCE = "WHSD: https://tinyurl.com/y3b83h53"

#     def __init__(self, osgrid_code):
#         super().__init__()
#         soil_texture_list = self._load_soil_data(osgrid_code)
#         self.update(self._return_soildata(osgrid_code, soil_texture_list))

#     def _load_soil_data(self, osgrid_code):
#         """
#         Load soil data from the WHSD postgreSQL database

#         --- NB ---
#         At the moment there is no script creating the database from
#         WHSD, and I am using an existing version underlying the NEV
#         suite of models.
#         """
#         soil_dict = get_whsd_data(osgrid_code, self._DEFAULT_SOILVARS)
#         return [value for _, value in soil_dict.items()]
