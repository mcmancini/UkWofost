# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), September 2023
# =========================================================
"""
Generate a Simulator which retrieves location and weather data
and allows to run multiple runs of the Wofost Crop yield model
based on a selected sampling strategy for the input parameter
space
"""

import pandas as pd
from pcse.base import ParameterProvider
# from pcse.models import Wofost80_NWLP_FD_beta
# from pcse.models import Wofost72_WLP_FD, LINGRA_WLP_FD
from pcse.db.nasapower import NASAPowerWeatherDataProvider
from pcse.models import LINGRA_WLP_FD, Wofost80_NWLP_FD_beta

from ukwofost.core.crop_manager import Crop, CropRotation
from ukwofost.core.defaults import defaults, wofost_parameters
from ukwofost.core.parcel import Parcel
from ukwofost.core.soil_manager import SoilGridsDataProvider
from ukwofost.core.utils import osgrid2lonlat
from ukwofost.core.weather_manager import (NetCDFWeatherDataProvider,
                                           ParcelWeatherDataProvider)


# pylint: disable=R0902
class WofostSimulator:
    """
    Class generating a Wofost simulator that allows to
    run Wofost on any location in GB and multiple times
    based on a list of input parameter sets.
    This is useful to perform sensitivity analysis or
    to build a Wofost emulator

    Input parameters for initialisation
    --------------------------------------------

    :param parcel: OS grid code of the location of interest
        or an instance of the Parcel class
    :param weather_provider (Str): either "Chess" (i.e., UKCEH
        ChessScape UKCP18 1km), "Custom" (i.e., weather data
        produced through data fusion and in csv format) or "NASA"
        (i.e., the default WOFOST NASA historic weather data provider)
    :param soil_provider: either "SoilGrids" or "WHSD", for SoilGrids
        soil data or World Harmonized Soil Database data. The latter
        does not yet have its data provider implemented, hence not
        yet available.

    Optional input parameters:
    :param **kwargs: a dictionary containing optional parameters
        such as "RCP", the RCP scenario of interest, or
        "ENSEMBLE", the climate ensemble member of interest.

    Methods defined here
    --------------------

    __str__(self, /)
        Return str(self).

    run(self, crop, **kwargs)
        run the Wofost simulator
    """

    _DEFAULT_RCP = defaults["rcp"]
    _DEFAULT_ENSEMBLE = defaults["ensemble"]

    wofost_params = wofost_parameters

    def __init__(self, parcel, weather_provider, soil_provider, **kwargs):
        self._parcel = parcel
        self._ensemble = kwargs.get("ENSEMBLE", self._DEFAULT_ENSEMBLE)
        self._rcp = kwargs.get("RCP", self._DEFAULT_RCP)
        self._weather_provider = weather_provider
        self._soil_provider = soil_provider

    @property
    def parcel_id(self):
        """Assign parcel ID"""
        return self._find_parcel_id(self._parcel)

    @property
    def osgrid_code(self):
        """Assign OS Grid code of the parcel centroid"""
        return self._find_oscode(self._parcel)

    @property
    def lon(self):
        """return longitude of parcel centroid"""
        return self._find_lonlat(self._parcel)["lon"]

    @property
    def lat(self):
        """return longitude of parcel centroid"""
        return self._find_lonlat(self._parcel)["lat"]

    @property
    def weather_provider(self):
        """Assign weather provider"""
        return self._weather_provider

    @property
    def wdp(self):
        """Return weather data"""
        return self._build_weather()

    @property
    def soildata(self):
        """Return soil data"""
        return self._build_soildata(self.osgrid_code, self._soil_provider)

    @property
    def sitedata(self):
        """Return site data"""
        return defaults.get("sitedata")

    @property
    def cropd(self):
        """Return crop parameter initialisator"""
        return defaults.get("cropd")

    @staticmethod
    def _find_parcel_id(parcel):
        """Retrieve parcel ID from parcel object"""
        if isinstance(parcel, str):
            parcel_id = parcel
        elif isinstance(parcel, Parcel):
            parcel_id = parcel.parcel_id
        else:
            parcel_id = None
            raise ValueError(
                f"{parcel} must be either an ID (str) or a Parcel instance."
            )
        return parcel_id

    @staticmethod
    def _find_oscode(parcel):
        """Retrieve parcel ID from parcel object"""
        if isinstance(parcel, str):
            os_code = parcel
        elif isinstance(parcel, Parcel):
            os_code = parcel.osgrid_code
        else:
            os_code = None
            raise ValueError(
                f"{parcel} must be either an ID (str) or a Parcel instance."
            )
        return os_code

    @staticmethod
    def _find_lonlat(parcel):
        """Find lon and lat of parcel"""
        if isinstance(parcel, str):
            lonlat = osgrid2lonlat(gridref=parcel, epsg=4326)
            lonlat_dict = {
                "lon": lonlat[0],
                "lat": lonlat[1],
            }
        elif isinstance(parcel, Parcel):
            lonlat = osgrid2lonlat(gridref=parcel.osgrid_code, epsg=4326)
            lonlat_dict = {
                "lon": lonlat[0],
                "lat": lonlat[1],
            }
        else:
            lonlat_dict = {
                "lon": None,
                "lat": None,
            }
            raise ValueError(
                f"{parcel} must be either an ID (str) or a Parcel instance."
            )
        return lonlat_dict

    # pylint: disable=R0913
    def _build_weather(self):
        if self.weather_provider == "NASA":
            wdp = NASAPowerWeatherDataProvider(latitude=self.lat, longitude=self.lon)
        elif self.weather_provider == "Chess":
            wdp = NetCDFWeatherDataProvider(self.osgrid_code, self._rcp, self._ensemble)
        elif self.weather_provider == "Custom":
            if isinstance(self._parcel, str):
                raise TypeError(
                    "Custom weather data can only be retrieved for parcels and not for"
                    " geographic coordinates"
                )
            wdp = ParcelWeatherDataProvider(parcel=self._parcel)
        else:
            wdp = None
            raise ValueError("weather provider can only be 'NASA', 'Chess' or 'Custom'")
        return wdp

    # pylint: enable=R0913

    @staticmethod
    def _build_soildata(os_code, soil_provider):
        if soil_provider == "SoilGrids":
            soildata = SoilGridsDataProvider(osgrid_code=os_code)
        elif soil_provider == "WHSD":
            soildata = None
            raise ValueError("WHSD soil data provider not yet implemented")
        else:
            soildata = None
            raise ValueError("Soil data provider can only be 'SoilGrids' or 'WHSD'")
        return soildata

    def run(self, crop_or_rotation, **kwargs):
        """
        Method to run Wofost for the crop specified in 'crop' and
        with default crop parameters unless custom parameters are
        specified in **kwargs
        :param crop_or_rotation: an instance of the class 'Crop'
               (see crop_manager.py for more info)
        :param **kwargs: optional dictionary with key-value pairs
               for any of the parameters that need to be customised:
               these only include the underlying WOFOST parameters
               (see wofost_params class attribute), but not agromanagement
               parameters. Non-default agromanagement parameters must be
               modified when initialising the instance of the class 'Crop'
               which is then passed to this method
        """
        if isinstance(crop_or_rotation, Crop):
            self.cropd.set_active_crop(crop_or_rotation.crop, crop_or_rotation.variety)

            # COMBINE ALL PARAMETERS
            parameters = ParameterProvider(
                cropdata=self.cropd, soildata=self.soildata, sitedata=self.sitedata
            )

            self._override_defaults(parameters, kwargs)

            # generate agromanagement
            crop_rotation = CropRotation([crop_or_rotation]).rotation

            # Run the model
            if crop_or_rotation.crop_type == "grass":
                wofsim = LINGRA_WLP_FD(parameters, self.wdp, crop_rotation)
                wofsim.run_till_terminate()
                summary_output = wofsim.get_summary_output()
                return summary_output[0]["WeightHARV"]

            # wofsim = Wofost72_WLP_FD(parameters, self.wdp, crop_rotation)
            wofsim = Wofost80_NWLP_FD_beta(parameters, self.wdp, crop_rotation)
            wofsim.run_till_terminate()
            # Collect output
            summary_output = wofsim.get_summary_output()
            return summary_output[0]["TWSO"]
            # pylint: enable=R0914

        if isinstance(crop_or_rotation, CropRotation):
            agromanagement = crop_or_rotation.rotation
            crop_name = next(iter(crop_or_rotation.crop_list[0]))
            crop_variety = crop_or_rotation.crop_list[0][crop_name]
            self.cropd.set_active_crop(crop_name, crop_variety)

            parameters = ParameterProvider(
                cropdata=self.cropd, soildata=self.soildata, sitedata=self.sitedata
            )

            self._override_defaults(parameters, kwargs)

            wofsim = Wofost80_NWLP_FD_beta(parameters, self.wdp, agromanagement)
            try:
                wofsim.run_till_terminate()
            # pylint: disable=W0718
            except Exception as e:
                print(
                    f"failed to run the WOFOST crop yield model for "
                    f"rotation '{crop_or_rotation}'"
                    f" due to {e}"
                )
            # pylint: enable=W0718
            output = wofsim.get_output()

            df = pd.DataFrame(output)
            df.set_index("day", inplace=True, drop=True)
            return df
        raise ValueError(f"Unsupported type: {type(crop_or_rotation)}")

    def _override_defaults(self, default_parameters, item):
        """
        Method to override the wofost parameters not associated with agromanagement.
        The list of such parameters is declared as a class attribute of the
        WofostSimulator class
        """
        default_parameters.clear_override()
        for key, value in item.items():
            if key in self.wofost_params:
                default_parameters.set_override(key, value)
            else:
                continue

    def __str__(self):
        msg = "======================================================\n"
        msg += "               Simulator characteristics\n"
        msg += "---------------------Description----------------------\n"
        msg += "Wofost simulator for location at '" + self.osgrid_code + "'" + "\n"
        msg += "Longitude: " + str(self.lon) + "\n"
        msg += "Latitude: " + str(self.lat) + "\n"
        msg += "Elevation: " + str(round(self.wdp.elevation, 2)) + "\n"
        msg += "Soil type: " + self.soildata["SOLNAM"] + "\n"
        return msg


# pylint: enable=R0902
