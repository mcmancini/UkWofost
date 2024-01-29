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
from pcse.models import Wofost80_NWLP_FD_beta, LINGRA_WLP_FD
from ukwofost.crop_manager import Crop, CropRotation
from ukwofost.defaults import defaults
from ukwofost.weather_manager import NetCDFWeatherDataProvider
from ukwofost.utils import osgrid2lonlat
from ukwofost.soil_manager import SoilGridsDataProvider

# from ukwofost.config import default_timed_events


# pylint: disable=R0902
class WofostSimulator:
    """
    Class generating a Wofost simulator that allows to
    run Wofost on any location in GB and multiple times
    based on a list of input parameter sets.
    This is useful to perform sensitivity analysis or
    to build a Wofost emulator
    --------------------------------------------------

    Required input parameters for initialisation:
    :param parcel_id: OS grid code of the location of interest

    Optional input parameters for initialisation
    :param **kwargs: a dictionary containing optional parameters
           such as "RCP", the RCP scenario of interest, or
           "ENSEMBLE", the climate ensemble member of interest.
           Here is also where a parameter to select alternative
           wheater data or soil data for the analysis will be
           selected (!not implemented yet!)

    Methods defined here:

    __str__(self, /)
        Return str(self).

    run(self, crop, **kwargs)
        run the Wofost simulator
    """

    _DEFAULT_RCP = defaults["rcp"]
    _DEFAULT_ENSEMBLE = defaults["ensemble"]

    wofost_params = set(
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

    def __init__(self, parcel_id, **kwargs):
        self.lon, self.lat = osgrid2lonlat(parcel_id, epsg=4236)
        self.osgrid_code = parcel_id

        self.ensemble = kwargs.get("ENSEMBLE", self._DEFAULT_ENSEMBLE)
        self.rcp = kwargs.get("RCP", self._DEFAULT_RCP)

        # weather
        self.wdp = NetCDFWeatherDataProvider(self.osgrid_code, self.rcp, self.ensemble)
        # soil
        self.soildata = SoilGridsDataProvider(self.osgrid_code)

        # site data
        self.sitedata = defaults.get("sitedata")

        # cropd
        self.cropd = defaults.get("cropd")

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
            # crop_start_date = crop_or_rotation.find_value("crop_start_date")
            self.cropd.set_active_crop(crop_name, crop_variety)
            parameters = ParameterProvider(
                cropdata=self.cropd, soildata=self.soildata, sitedata=self.sitedata
            )
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
