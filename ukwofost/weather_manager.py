# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), June 2023
# ====================================================
"""
A weather data provider reading its data from netCDF files.
Code based on the 'excelweatherdataprovider contained in the
fileinput of the PCSE module
"""
import os
import datetime as dt
import xarray as xr
import pandas as pd
from pcse.base import WeatherDataContainer, WeatherDataProvider
from pcse.util import reference_ET, check_angstromAB
from pcse.exceptions import PCSEError
from pcse.db import NASAPowerWeatherDataProvider
from pcse.settings import settings
from ukwofost import app_config
from ukwofost.utils import (
    osgrid2lonlat,
    rh_to_vpress,
    calc_doy,
    nearest,
    find_closest_point,
    get_dtm_values,
)

# from ukwofost.db_manager import get_parcel_data, get_dtm_values


# Conversion functions
def no_conversion(x):
    """
    mapping function for no unit conversion
    """
    return x


def k_to_c(x):
    """
    Mapping function for conversion from degrees K to C
    """
    return x - 273.15


def flux_to_cm(x):
    """
    Mapping function for conversion from precipitation flux
    to cm/day
    """
    return x * 86400 / 10.0


# Declare NetCDFWeatherDataProvider class
# pylint: disable=R0902
class NetCDFWeatherDataProvider(WeatherDataProvider):
    """Reading weather data from a NetCDF file (.nc).

    :param osgrid_code: code of the OS tile for which weather projections are required
    :param rcp: the rcp scenario for which weather projections are required
    :param ensemble: the ensemble for the rcp for which weather projections are required
    :param mising_snow_depth: the value that should use for missing SNOW_DEPTH values,
           the default value is `None`.
    :param force_update: bypass the cache file, reload data from the netcdf files and
           write a new cache file. Cache files are written under
           `$HOME/.pcse/meteo_cache`

    The NetCDFWeatherDataProvider takes care of the adjustment of solar radiation to the
    length of the day (AAA: need to verify that the solar radiation data passed to
    compute ETs is the data expected by the functions implemented in Wofost!!!) and
    deals with the fact that the length of a year in ChessScape is 360 days, which
    Wofost cannot handle.
    """

    obs_conversions = {
        "TMAX": k_to_c,
        "TMIN": k_to_c,
        "IRRAD": no_conversion,
        "VAP": no_conversion,
        "WIND": no_conversion,
        "RAIN": flux_to_cm,
        "SNOWDEPTH": no_conversion,
    }

    # pylint: disable=R0913
    def __init__(
        self,
        osgrid_code,
        rcp,
        ensemble,
        missing_snow_depth=None,
        nodata_value=-999,
        force_update=False,
    ):
        WeatherDataProvider.__init__(self)

        os_digits = [int(s) for s in osgrid_code if s.isdigit()]
        os_digits_1k = (
            os_digits[0:2]
            + os_digits[int(len(os_digits) / 2) : int(len(os_digits) / 2 + 2)]
        )
        os_digits_10k = (
            os_digits[0:1]
            + os_digits[int(len(os_digits) / 2) : int(len(os_digits) / 2 + 1)]
        )
        os_digits_1k = "".join(str(s) for s in os_digits_1k)
        os_digits_10k = "".join(str(s) for s in os_digits_10k)
        self.osgrid_1km = osgrid_code[0:2].upper() + os_digits_1k
        self.osgrid_10km = osgrid_code[0:2].upper() + os_digits_10k
        # pylint: disable=E1101
        self.nc_fname = (
            app_config.data_dirs["climate_dir"]
            + f"{self.osgrid_10km.upper()}_{rcp}_{ensemble:02d}.nc"
        )
        self.rcp, self.ensemble = rcp, ensemble
        self.missing_snow_depth = missing_snow_depth
        self.nodata_value = nodata_value
        self.cache_fname = f"{self.osgrid_1km}_{self.rcp}_{self.ensemble:02d}"
        if not os.path.exists(self.nc_fname):
            msg = f"Cannot find weather file at: {self.nc_fname}"
            raise PCSEError(msg)

        self.longitude, self.latitude = osgrid2lonlat(self.osgrid_1km, epsg=4326)

        # Retrieve altitude
        # self.elevation = get_parcel_data(osgrid_code, ['elevation'])['elevation']
        self.elevation = get_dtm_values(osgrid_code, app_config)["elevation"]
        # pylint: enable=E1101

        # Retrieve Angstrom coefficients A and B
        w = NASAPowerWeatherDataProvider(
            latitude=self.latitude, longitude=self.longitude
        )
        # pylint: disable=C0103
        self.angstA, self.angstB = check_angstromAB(w.angstA, w.angstB)
        # pylint: enable=C0103

        # Check for existence of a cache file
        cache_file = self._find_cache_file(self.cache_fname)
        if cache_file is None or force_update is True:
            msg = (
                "No cache file or forced update, "
                "getting data from Chess-Scape nc files."
            )
            self.logger.debug(msg)
            # No cache file, we really have to get the data from the
            # Chess-Scape nc files
            self._get_and_process_chessscape()
            return

        # get age of cache file, if age < 90 days then try to load it.
        # If loading fails retrieve data from the Chess-Scape nc files.

        age = (
            dt.date.today() - dt.date.fromtimestamp(os.stat(cache_file).st_mtime)
        ).days
        if age < 90:
            self.logger.debug(
                "Start loading weather data from cache file: %s", cache_file
            )

            if self._load_cache_file(self.cache_fname) is not True:
                self.logger.debug(
                    "Loading cache file failed, "
                    "reloading data from Chess-Scape nc files."
                )
                # Loading cache file failed!
                self._get_and_process_chessscape()
        else:
            # Cache file is too old. Try loading new data from ChessScape
            try:
                self.logger.debug(
                    "Cache file older then 90 days, "
                    "reloading from Chess-Scape nc files."
                )
                self._get_and_process_chessscape()
            except FileNotFoundError as exc:
                msg = (
                    f"Reloading data from Chess-Scape nc files failed, "
                    f"reverting to (outdated) "
                    f" {cache_file}"
                )
                self.logger.debug(msg)
                if self._load_cache_file(self.cache_fname) is not True:
                    msg = "Outdated cache file failed loading."
                    raise PCSEError(msg) from exc

    def _create_header(self):
        country = "Great Britain"
        desc = (
            f"Projected weather for OS tile '{self.osgrid_1km}', "
            f"{self.rcp} and ensemble {self.ensemble}"
        )
        src = "UK Centre for Ecology and Hydrology"
        contact = "Emma Robinson at emrobi@ceh.ac.uk"
        self.description = [
            "Weather data for:",
            f"Country: {country}",
            f"Station: {self.osgrid_1km}",
            f"Description: {desc}",
            f"Source: {src}",
            f"Contact: {contact}",
        ]

    def _get_and_process_chessscape(self):
        # Initial preparation of weather data
        lon, lat = osgrid2lonlat(self.osgrid_1km)
        os_array = xr.open_dataset(self.nc_fname)

        os_dataframe = (
            os_array.sel(x=lon, y=lat, method="nearest").to_dataframe().reset_index()
        )
        # There is  a posibility that the assignment of weather data to parcels
        # near the coastline could result in empty data (nan). This is because the
        # .sel("closest") method in xarray is based on the x-y coordinates,
        # regardless of whether the arrays at those coordinates are
        # empty or not. Deal with this selecting the closest non-null cell.
        # (Euclidean distance)
        if os_dataframe.isnull().any().any():
            os_array.sel(x=lon, y=lat, method="nearest").to_dataframe().reset_index()
            os_dataframe = (
                os_array.where(
                    (os_array.x >= lon - 10000)
                    & (os_array.x < lon + 10000)
                    & (os_array.y >= lat - 10000)
                    & (os_array.y < lat + 10000),
                    drop=True,
                )
                .to_dataframe()
                .reset_index()
            )
            os_dataframe = os_dataframe.dropna()
            unique_combinations = (
                os_dataframe[["y", "x"]].drop_duplicates().to_dict(orient="records")
            )
            closest = find_closest_point(unique_combinations, lon, lat)
            os_dataframe = os_dataframe[
                (os_dataframe["x"] == closest["x"])
                & (os_dataframe["y"] == closest["y"])
            ]
        vap = [
            rh_to_vpress(x, y)
            for x, y in zip(os_dataframe["hurs"], os_dataframe["tas"] - 273.15)
        ]
        os_dataframe = os_dataframe[
            os_dataframe.columns.drop(
                ["lat", "lon", "x", "y", "tas", "rds", "rlds", "hurs"]
            )
        ]
        os_dataframe.columns = ["DAY", "TMAX", "TMIN", "RAIN", "IRRAD", "WIND"]
        os_dataframe["SNOWDEPTH"] = -999
        os_dataframe["VAP"] = vap

        # chess-scape data is based on 360 day years, which breaks Wofost.
        # Convert to datetime and interpolate missing data
        os_dataframe["DAY"] = [calc_doy(x) for x in os_dataframe["DAY"]]
        os_dataframe.set_index(["DAY"], inplace=True)
        date_rng = pd.date_range(
            os_dataframe.index[0], os_dataframe.index[-1], freq="D"
        )
        date_rng = [x.date() for x in date_rng]
        missing_days = list(set(date_rng).difference(os_dataframe.index))
        for day in missing_days:
            nearest_day = nearest(day, os_dataframe.index)
            nearest_vals = (
                os_dataframe.loc[nearest_day, :].to_frame().transpose().reset_index()
            )
            nearest_vals["index"] = day
            nearest_vals.set_index("index", inplace=True)
            nearest_vals.index.rename("DAY", inplace=True)
            os_dataframe = pd.concat([os_dataframe, nearest_vals])

        os_dataframe.sort_index(ascending=True, inplace=True)

        # adjust irradiation for lenght of the day
        os_dataframe["IRRAD"] = os_dataframe["IRRAD"] * 3600 * 24
        self._read_observations(os_dataframe)

        # dump contents to a cache file
        cache_filename = self._get_cache_filename(self.cache_fname)
        self._dump(cache_filename)

    def _read_observations(self, os_dataframe):
        climate_data = os_dataframe.reset_index()

        # First get the column labels
        labels = list(climate_data.columns)

        # Start reading all rows with data
        # rownums = list(range(sheet.nrows))
        for row in range(len(climate_data)):
            try:
                climate_dict = {}
                for label in labels:
                    if label == "DAY":
                        if climate_data.iloc[row, :][label] is None:
                            raise ValueError
                        doy = climate_data.iloc[row, :][label]
                        climate_dict[label] = doy
                        continue

                    # explicitly convert to float. If this fails a ValueError
                    # will be thrown
                    value = climate_data.iloc[row, :][label]

                    # Check for observations marked as missing. Currently only missing
                    # data is allowed for SNOWDEPTH. Otherwise raise an error
                    if self._is_missing_value(value):
                        if label == "SNOWDEPTH":
                            value = self.missing_snow_depth
                        else:
                            raise ValueError()

                    func = self.obs_conversions[label]
                    climate_dict[label] = func(value)

                # Reference ET in mm/day
                e0, es0, et0 = reference_ET(
                    LAT=self.latitude,
                    ELEV=self.elevation,
                    ANGSTA=self.angstA,
                    ANGSTB=self.angstB,
                    **climate_dict,
                )
                # convert to cm/day
                climate_dict["E0"] = e0 / 10.0
                climate_dict["ES0"] = es0 / 10.0
                climate_dict["ET0"] = et0 / 10.0

                wdc = WeatherDataContainer(
                    LAT=self.latitude,
                    LON=self.longitude,
                    ELEV=self.elevation,
                    **climate_dict,
                )
                self._store_WeatherDataContainer(wdc, climate_dict["DAY"])

            except ValueError:  # strange value in cell
                self.logger.warning("Failed reading row: %i. Skipping...", row)
                print(f"Failed reading row: {row}. Skipping...")

    def _find_cache_file(self, cache_fname):
        """Try to find a cache file for given latitude/longitude.

        Returns None if the cache file does not exist, else it returns the full path
        to the cache file.
        """
        cache_filename = self._get_cache_filename(cache_fname)
        if os.path.exists(cache_filename):
            return cache_filename
        return None

    def _get_cache_filename(self, cache_fname):
        """Constructs the filename used for cache files given latitude and longitude

        The file name is constructed combining the class name, the OS 1km tile
        code, the rcp code and the ensemble
        (i.e.: NetCDFWeatherDataProvider_SX7347_rcp26_01.cache)
        """
        fname = f"{self.__class__.__name__}_{cache_fname}.cache"
        # pylint: disable=E1101
        cache_filename = os.path.join(settings.METEO_CACHE_DIR, fname)
        # pylint: enable=E1101
        return cache_filename

    def _load_cache_file(self, cache_fname):
        """Loads the data from the cache file. Return True if successful."""
        cache_filename = self._get_cache_filename(cache_fname)
        try:
            self._load(cache_filename)
            msg = "Cache file successfully loaded."
            self.logger.debug(msg)
            return True
        except (IOError, EnvironmentError, EOFError) as e:
            msg = f"Failed to load cache from file '{cache_filename}' due to: {e}"
            self.logger.warning(msg)
            return False

    def _is_missing_value(self, value):
        """Checks if value is equal to the value specified for missing date
        :return: True|False
        """
        eps = 0.0001
        if abs(value - self.nodata_value) < eps:
            return True
        return False

    # pylint: enable=R0913


# pylint: enable=R0902
