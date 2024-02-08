# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), September 2023
# =========================================================
"""
Utility functions to be used in the UK implementation of the
WOFOST crop yield model.
============================================================

Classes defined here:
---------------------

sun()
    Generates a sun() object which allows to compute the duration
    of the day for a specified date


Functions defined here:
-----------------------

lonlat2osgrid(coords, figs)
    converts a lon-lat pair to an OS grid code

osgrid2bbox(gridref, os_cellsize)
    Convert British National Grid references to OSGB36 numeric
    coordinates of the bounding box of the 10km grid or 100km grid
    squares.

osgrid2lonlat(gridref, epsg)
    Convert British National Grid references to OSGB36 numeric
    coordinates. Grid references can be 4, 6, 8 or 10 figures

rh_to_vpress(rel_humidity, temp)
    Conversion from relative humidity to vapour pressure

rescale_windspeed(windspeed, measured_height)
    Estimate wind speed at 2m height from wind speed measured
    at 'measured_height'.

net_radiation(shortwave_flux, longwave_flux, day_length)
    Calculate net radiation at the surface based on duration of
    the day

find_closest_cell(parcel_centroid, climate_cells)
    Given a parcel and its centroid, find the ID of the closest
    Chess-Scape climate cell

calc_doy(cftime_day):
    Converts a 360-based datetime object (cfttime) to a standard
    datetime object.

nearest(item, valuelist):
    Find nearest value to item in valuelist

find_closest_point(points, x, y):
     Given a list of points defined by x and y coordinates, find
    the closest one to a user-defined location characterised by
    coordinates 'x' and 'y'

water_retention(x, theta_r, theta_s, alpha, npar):
    Function that generates a soil water retention curve based on
    the van Genuchten model

water_conductivity(x, theta_r, theta_s, alpha, npar, k_sat):
    Unsaturated water conductivity function.

date_to_int(date_to_convert, reference)
    Convert date to integer computing the number
    of days passed from 'reference' to 'date'

int_to_date(int_to_convert, reference=None)
    Convert an integer (number of days) to a datetime date
    using the specified reference date

get_dtm_values(parcel_os_code, app_config)
    Query the DTM database based on longitude and latitude to
    retrieve elevation, slope and aspect

find_contiguous_sets(data_frame, col_name)
    Returns ordinal indices of contiguous non-NA values in
    a column of a dataframe that contains NAs and non-NA
    values.
"""

import math
from math import exp, log, cos, sin, acos, asin, tan, floor
from math import degrees as deg, radians as rad
from datetime import date, datetime, time, timedelta
import re
import pandas as pd
import psycopg2
from pyproj import Transformer


class BNGError(Exception):
    """Exception raised by OSgrid coordinate conversion functions"""


def _init_regions_and_offsets():
    # Region codes for 100 km grid squares.
    regions = [
        ["HL", "HM", "HN", "HO", "HP", "JL", "JM"],
        ["HQ", "HR", "HS", "HT", "HU", "JQ", "JR"],
        ["HV", "HW", "HX", "HY", "HZ", "JV", "JW"],
        ["NA", "NB", "NC", "ND", "NE", "OA", "OB"],
        ["NF", "NG", "NH", "NJ", "NK", "OF", "OG"],
        ["NL", "NM", "NN", "NO", "NP", "OL", "OM"],
        ["NQ", "NR", "NS", "NT", "NU", "OQ", "OR"],
        ["NV", "NW", "NX", "NY", "NZ", "OV", "OW"],
        ["SA", "SB", "SC", "SD", "SE", "TA", "TB"],
        ["SF", "SG", "SH", "SJ", "SK", "TF", "TG"],
        ["SL", "SM", "SN", "SO", "SP", "TL", "TM"],
        ["SQ", "SR", "SS", "ST", "SU", "TQ", "TR"],
        ["SV", "SW", "SX", "SY", "SZ", "TV", "TW"],
    ]

    # Transpose so that index corresponds to offset
    regions = list(zip(*regions[::-1]))

    # Create mapping to access offsets from region codes
    offset_map = {}
    for i, row in enumerate(regions):
        for j, region in enumerate(row):
            offset_map[region] = (1e5 * i, 1e5 * j)

    return regions, offset_map


_regions, _offset_map = _init_regions_and_offsets()


def lonlat2osgrid(coords, figs=4):
    """
    Convert WGS84 lon-lat coordinates to British National Grid references.
    Grid references can be 4, 6, 8 or 10 fig, specified by the figs keyword.
    Adapted from John A. Stevenson's 'bng' package that can be found at
    https://pypi.org/project/bng/

    :param coords: tuple - x, y coordinates to convert
    :param figs: int - number of figures to output
    :return gridref: str - BNG grid reference

    Examples:

    Single value
    >>> lonlat2osgrid((-5.21469, 49.96745))

    For multiple values, use Python's zip function and list comprehension
    >>> x = [-5.21469, -5.20077, -5.18684]
    >>> y = [49.96745, 49.96783, 49.96822]
    >>> [lonlat2osgrid(coords, figs=4) for coords in zip(x, y)]
    """
    # Validate input
    bad_input_message = (
        f"Valid inputs are x, y tuple e.g. (-5.21469, 49.96783),"
        f" or list of x, y tuples. [{coords}]"
    )

    if not isinstance(coords, tuple):
        raise BNGError(bad_input_message)

    try:
        # convert to WGS84 to OSGB36 (EPSG:27700)
        # pylint: disable=E0633
        transformer = Transformer.from_crs(4326, 27700, always_xy=True)
        x_coord, y_coord = transformer.transform(coords[0], coords[1])
        # pylint: enable=E0633
    except ValueError as exc:
        raise BNGError(bad_input_message) from exc

    out_of_region_message = f"Coordinate location outside UK region: {coords}"
    if (x_coord < 0) or (y_coord < 0):
        raise BNGError(out_of_region_message)

    # Calculate region and SW corner offset

    try:
        region = _regions[int(floor(x_coord / 100000.0))][
            int(floor(y_coord / 100000.0))
        ]
        x_offset, y_offset = _offset_map[region]
    except IndexError as exc:
        raise BNGError(out_of_region_message) from exc

    # Format the output based on figs
    templates = {
        4: "{}{:02}{:02}",
        6: "{}{:03}{:03}",
        8: "{}{:04}{:04}",
        10: "{}{:05}{:05}",
    }
    factors = {4: 1000.0, 6: 100.0, 8: 10.0, 10: 1.0}
    try:  # Catch bad number of figures
        coords = templates[figs].format(
            region,
            int(floor((x_coord - x_offset) / factors[figs])),
            int(floor((y_coord - y_offset) / factors[figs])),
        )
    except KeyError as exc:
        raise BNGError("Valid inputs for figs are 4, 6, 8 or 10") from exc

    return coords


def osgrid2bbox(gridref, os_cellsize):
    """
    Convert British National Grid references to OSGB36 numeric coordinates.
    of the bounding box of the 10km grid or 100km grid squares.
    Grid references can be 2, 4, 6, 8 or 10 figures.

    :param gridref: str - BNG grid reference
    :returns coords: dictionary {xmin, xmax, ymin, ymax}

    Examples:

    Single value
    >>> osgrid2bbox('NT2755072950', '10km')
    {'xmin': 320000, 'xmax': 330000, 'ymin': 670000, 'ymax': 680000}

    For multiple values, use Python's zip function and list comprehension
    >>> gridrefs = ['HU431392', 'SJ637560', 'TV374354']
    >>> [osgrid2bbox(g, '10km') for g in gridrefs]
    >>> [{'xmin': 440000, 'xmax': 450000, 'ymin': 1130000, 'ymax': 1140000},
        {'xmin': 360000, 'xmax': 370000, 'ymin': 330000, 'ymax': 340000},
        {'xmin': 530000, 'xmax': 540000, 'ymin': 70000, 'ymax': 80000}]
    """
    # Validate input
    bad_input_message = (
        f"Valid gridref inputs are 2 characters and none, "
        f"2, 4, 6, 8 or 10-fig references as strings "
        f'e.g. "NN123321", or lists/tuples/arrays of strings. '
        f"[{gridref}]"
    )

    gridref = gridref.upper()
    if os_cellsize == "10km":
        try:
            pattern = r"^([A-Z]{2})(\d{2}|\d{4}|\d{6}|\d{8}|\d{10})$"
            match = re.match(pattern, gridref)
            # Extract data from gridref
            region, coords = match.groups()
        except (TypeError, AttributeError) as exc:
            # Non-string values will throw error
            raise BNGError(bad_input_message) from exc
    elif os_cellsize == "100km":
        try:
            pattern = r"^([A-Z]{2})"
            match = re.match(pattern, gridref)
            # Extract data from gridref
            region = match.groups()[0]
        except (TypeError, AttributeError) as exc:
            raise BNGError(bad_input_message) from exc
    else:
        raise BNGError(
            "Invalid argument 'os_cellsize' supplied: "
            "values can only be '10km' or '100km'"
        )

    # Get offset from region
    try:
        _offset_map[region]
    except KeyError as exc:
        raise BNGError(f"Invalid grid square code: {region}") from exc

    # Get easting and northing from text and convert to coords
    if os_cellsize == "10km":
        coords = coords[0:2]  # bbox is for each 10km cell!
        easting = int(coords[: (len(coords) // 2)])
        northing = int(coords[(len(coords) // 2) :])
        scale_factor = 10 ** (5 - (len(coords) // 2))
        x_min = int(easting * scale_factor + _offset_map[region][0])
        y_min = int(northing * scale_factor + _offset_map[region][1])
        x_max = int(easting * scale_factor + _offset_map[region][0] + 1e4)
        y_max = int(northing * scale_factor + _offset_map[region][1] + 1e4)
    elif os_cellsize == "100km":
        x_min = int(_offset_map[region][0])
        y_min = int(_offset_map[region][1])
        x_max = int(_offset_map[region][0] + 1e5)
        y_max = int(_offset_map[region][1] + 1e5)
    else:
        raise BNGError(
            "Invalid argument 'os_cellsize' "
            "supplied: values can only be '10km' or '100km'"
        )

    return {"xmin": x_min, "xmax": x_max, "ymin": y_min, "ymax": y_max}


def osgrid2lonlat(gridref, epsg=None):
    """
    Convert British National Grid references to OSGB36 numeric coordinates.
    Grid references can be 4, 6, 8 or 10 figures.

    :param gridref: str - BNG grid reference
    :returns coords: tuple - x, y coordinates

    Examples:

    Single value
    >>> osgrid2lonlat('NT2755072950')
    (327550, 672950)

    For multiple values, use Python's zip function and list comprehension
    >>> gridrefs = ['HU431392', 'SJ637560', 'TV374354']
    >>> x, y = zip(*[osgrid2lonlat(g) for g in gridrefs])
    >>> x
    (443100, 363700, 537400)
    >>> y
    (1139200, 356000, 35400)
    """
    # Validate input
    bad_input_message = (
        f"Valid gridref inputs are 4, 6, 8 or 10-fig references as strings "
        f'e.g. "NN123321", or lists/tuples/arrays of strings. \'[{gridref}]'
    )

    try:
        gridref = gridref.upper()
        pattern = r"^([A-Z]{2})(\d{4}|\d{6}|\d{8}|\d{10})$"
        match = re.match(pattern, gridref)
    except (TypeError, AttributeError) as exc:
        # Non-string values will throw error
        raise BNGError(bad_input_message) from exc

    if not match:
        raise BNGError(bad_input_message)

    # Extract data from gridref
    region, coords = match.groups()

    # Get offset from region
    try:
        _offset_map[region]
    except KeyError as exc:
        raise BNGError(f"Invalid 100 km grid square code: {region}") from exc

    # Get easting and northing from text and convert to coords

    easting = int(coords[: (len(coords) // 2)])
    northing = int(coords[(len(coords) // 2) :])
    scale_factor = 10 ** (5 - (len(coords) // 2))
    x_coord = int(easting * scale_factor + _offset_map[region][0])
    y_coord = int(northing * scale_factor + _offset_map[region][1])

    if epsg is None:
        return x_coord, y_coord

    try:
        transformer = Transformer.from_crs(27700, epsg, always_xy=True)
        return transformer.transform(x_coord, y_coord)
    except Exception as exc:
        raise BNGError("Invalid EPSG code provided") from exc


# pylint: disable=R0902
class Sun:
    """
    Calculate duration of the day based on NOAA
    https://gml.noaa.gov/grad/solcalc/calcdetails.html

    Typical use
    -----------
    from datetime import date
    a = Sun(lat=41.0082, long=28.9784)
    when = date(2022, 10, 14)
    print('sunrise at ', a.sunrise(when))
    print('sunset at ', a.sunset(when))
    print(f'day length of {a.daylength(when)} hours')

    """

    def __init__(self, lat=50.7260, long=3.5275):  # default Exeter
        self.lat = lat
        self.long = long
        self.day = None
        self.time = None
        self.timezone = None
        self.solarnoon_t = None
        self.sunrise_t = None
        self.sunset_t = None
        self.daylength_t = None

    def daylength(self, when):
        """
        return the length in hours (decimal) of the day
        specified in 'when', for lat and long, and passed
         as a datetime.date object.
        """
        self.__preptime(when)
        self.__calc()
        return Sun.__lengthfromdecimaldiff(self.daylength_t)

    def sunrise(self, when):
        """Return time of sunrise, UTC"""
        self.__preptime(when)
        self.__calc()
        return Sun.__timefromdecimal(self.sunrise_t)

    def sunset(self, when):
        """Return time of sunset, UTC"""
        self.__preptime(when)
        self.__calc()
        return Sun.__timefromdecimal(self.sunset_t)

    def noon(self, when):
        """Return time of solar noon, UTC"""
        self.__preptime(when)
        self.__calc()
        return Sun.__timefromdecimal(self.solarnoon_t)

    @staticmethod
    def __timefromdecimal(day):
        """
        returns a datetime.time object.
        day is a decimal day between 0.0 and 1.0, e.g. noon = 0.5
        """

        hours = 24.0 * day
        minutes = (hours - int(hours)) * 60
        seconds = (minutes - int(minutes)) * 60
        return time(hour=int(hours), minute=int(minutes), second=int(seconds))

    @staticmethod
    def __lengthfromdecimaldiff(hours):
        """Return a number of hours from a decimal length of a day"""
        return hours * 24

    def __preptime(self, when):
        """
        Extract information in a suitable format from when,
        a datetime.date object.
        """
        # datetime days are numbered in the Gregorian calendar
        # while the calculations from NOAA are distibuted as
        # OpenOffice spreadsheets with days numbered from
        # 1/1/1900. The difference are those numbers taken for
        # 18/12/2010
        dtime = datetime.combine(when, time(12, 0, 0))
        self.day = dtime.toordinal() - (734123 - 40529)
        adj_t = dtime.time()
        self.time = (adj_t.hour + adj_t.minute / 60.0 + adj_t.second / 3600.0) / 24.0

        self.timezone = 0
        offset = dtime.utcoffset()
        if not offset is None:
            self.timezone = offset.seconds / 3600.0

    def __calc(self):
        """
        Perform the actual calculations for sunrise, sunset and
        a number of related quantities.
        The results are stored in the instance variables
        sunrise_t, sunset_t and solarnoon_t
        """
        julian_day = self.day + 2415018.5 + self.time - self.timezone / 24
        julian_century = (julian_day - 2451545) / 36525
        gmls = (
            280.46646 + julian_century * (36000.76983 + julian_century * 0.0003032)
        ) % 360
        gmas = 357.52911 + julian_century * (35999.05029 - 0.0001537 * julian_century)
        eeo = 0.016708634 - julian_century * (
            0.000042037 + 0.0000001267 * julian_century
        )
        seqcent = (
            sin(rad(gmas))
            * (1.914602 - julian_century * (0.004817 + 0.000014 * julian_century))
            + sin(rad(2 * gmas)) * (0.019993 - 0.000101 * julian_century)
            + sin(rad(3 * gmas)) * 0.000289
        )
        sapplong = (
            gmls
            + seqcent
            - 0.00569
            - 0.00478 * sin(rad(125.04 - 1934.136 * julian_century))
        )
        obcorr = (
            23
            + (
                26
                + (
                    21.448
                    - julian_century
                    * (46.815 + julian_century * (0.00059 - julian_century * 0.001813))
                )
                / 60
            )
            / 60
        ) + 0.00256 * cos(rad(125.04 - 1934.136 * julian_century))
        sdec = deg(asin(sin(rad(obcorr)) * sin(rad(sapplong))))
        var_y = tan(rad(obcorr / 2)) * tan(rad(obcorr / 2))
        t_eq = 4 * deg(
            var_y * sin(2 * rad(gmls))
            - 2 * eeo * sin(rad(gmas))
            + 4 * eeo * var_y * sin(rad(gmas)) * cos(2 * rad(gmls))
            - 0.5 * var_y * var_y * sin(4 * rad(gmls))
            - 1.25 * eeo * eeo * sin(2 * rad(gmas))
        )
        ha_srise = deg(
            acos(
                cos(rad(90.833)) / (cos(rad(self.lat)) * cos(rad(sdec)))
                - tan(rad(self.lat)) * tan(rad(sdec))
            )
        )
        self.solarnoon_t = (720 - 4 * self.long - t_eq + self.timezone * 60) / 1440
        self.sunrise_t = (self.solarnoon_t * 1440 - ha_srise * 4) / 1440
        self.sunset_t = (self.solarnoon_t * 1440 + ha_srise * 4) / 1440
        self.daylength_t = self.sunset_t - self.sunrise_t


# pylint: enable=R0902


def rh_to_vpress(rel_humidity, temp):
    """
    Conversion from relative humidity to vapour pressure
    in hPa (or mm) using the Clausius-Clapeyron relationship
    See https://bit.ly/3e4VZKI (Hartmann, 1994). The latent
    heat of vaporization depends on temperature as well. Use
    curve from Osborne et al. (1930, 1937), obtained from
    https://bit.ly/2LXYLAO
    """
    t_base = (0.01, 2, 4, 10, 14, 18, 20, 25, 30, 34, 40, 44, 50)
    hvap = (
        2500.9,
        2496.2,
        2491.4,
        2477.2,
        2467.7,
        2458.3,
        2453.5,
        2441.7,
        2429.8,
        2420.3,
        2406.0,
        2396.4,
        2381.9,
    )
    nearest_t_idx = min(range(len(t_base)), key=lambda i: abs(t_base[i] - (temp)))
    vps = 6.11 * exp(
        ((hvap[nearest_t_idx] * 1e3) / 461) * (1 / 273.15 - 1 / (temp + 273.15))
    )
    vapour_pressure = vps * (rel_humidity / 100)
    return vapour_pressure


def rescale_windspeed(windspeed, measured_height):
    """
    Estimate wind speed at 2m height from wind speed measured
    at 'measured_height'.
    UKCP18 wind speed is been estimated at a height of 10m but
    the Penman equation requires wind values at 2m height.
    Conversion is done with the formula presented in
    https://bit.ly/3fOP34P
    Notes: windspeeds must be in m/s
    """
    base_windspeed = windspeed * (4.87 / log(67.8 * measured_height - 5.42))
    return base_windspeed


def net_radiation(shortwave_flux, longwave_flux, day_length):
    """
    Calculate net radiation at the surface summing total shortwave and
    longwave fluxes (these are the total downward fluxes: rsds and rlds,
    d for downward). Convert values from W/m2 to J/m2/d based on the
    length of the day in decimal hours. Cloud cover has already been
    accounted for in the magnitude of fluxes

    """
    tot_rad = shortwave_flux + longwave_flux
    irrad = tot_rad * day_length * 3600
    return irrad


def find_closest_cell(parcel_centroid, climate_cells):
    """
    Given a parcel and its centroid, find the ID of the closest
    Chess-Scape climate cell.
    Both parcel_centroid and climate_cells must be spatial objects
    (GeoPandas); wihle the parcel centroid is a single point,
    climate_cells is a spatial series of all Chess-Scape cells.
    """
    dst = [
        parcel_centroid.distance(climate_cells.values[ind])
        for ind in range(climate_cells.shape[0])
    ]
    (val, idx) = min((val, idx) for idx, val in enumerate(dst))
    return idx


def calc_doy(cftime_day):
    """
    Converts a 360-based datetime object (cfttime) to a standard
    datetime object. The assumption here is that hte last 5 days
    of December in a given year are missing.
    """
    doy = date.fromordinal(cftime_day.dayofyr)
    doy = doy.replace(year=cftime_day.year)
    return doy


def nearest(item, valuelist):
    """
    Find nearest value to item in valuelist
    """
    return min(valuelist, key=lambda x: abs(x - item))


def find_closest_point(points, x_coord, y_coord):
    """
     Given a list of points defined by x and y coordinates, find
    the closest one to a user-defined location characterised by
    coordinates 'x' and 'y'
    :param points: a list of dictionaries [{'x':a, 'y':b},{'x':c, 'y':d}]
    :param x: an EPSG:27700 longitude value
    :param y: an EPSG:27700 latitude value
    """
    closest_point = None
    closest_distance = float("inf")
    for point in points:
        distance = math.sqrt((point["x"] - x_coord) ** 2 + (point["y"] - y_coord) ** 2)
        if distance < closest_distance:
            closest_distance = distance
            closest_point = point
    return closest_point


def water_retention(matric_potential, theta_r, theta_s, alpha, npar):
    """
    Function that generates a soil water retention curve based on
    the van Genuchten model. This depends on a set of parameters
    which are estimated based on soil characteristics.
    Output in cm3/cm3
    See https://tinyurl.com/3knz4wsn
    An example of a model that estimates the water retention
    parameters is the USDA Rosetta model
    https://github.com/usda-ars-ussl/rosetta-soil
    """
    psi = 10.0**matric_potential
    m_coeff = 1 - 1 / npar
    num = theta_s - theta_r
    denom = (1 + abs(alpha * psi) ** npar) ** m_coeff
    water_ret = theta_r + num / denom
    return water_ret


# pylint: disable=R0913
def water_conductivity(matric_potential, theta_r, theta_s, alpha, npar, k_sat):
    """
    Unsaturated water conductivity function. Generated
    from the parametric formulation of van Genuchten
    in combination with the Mualem model.
    See https://tinyurl.com/3knz4wsn
    Output in cm/d
    """
    theta = water_retention(matric_potential, theta_r, theta_s, alpha, npar)
    m_coeff = 1 - 1 / npar
    w_content = (theta - theta_r) / (theta_s - theta_r)
    se_l = (
        w_content**0.5
    )  # parameter describing the pore structure of the material usually set to 0.5
    se_m = w_content ** (1 / m_coeff)
    se_fact = (1 - se_m) ** m_coeff
    k_rel = se_l * (1 - se_fact) * (1 - se_fact)
    k_psi = k_sat * k_rel
    return k_psi


# pylint: enable=R0913


def date_to_int(date_to_convert, reference=None):
    """
    Convert date to integer computing the number
    of days passed from 'reference' to 'date'
    """
    if reference is None:
        reference = datetime(1900, 1, 1)

    days_since_reference = (date_to_convert - reference).days

    return days_since_reference


def int_to_date(int_to_convert, reference=None):
    """
    Convert an integer (number of days) to a datetime date
    using the specified reference date.
    """
    if reference is None:
        reference = datetime(
            1900, 1, 1
        )  # Default reference date (e.g., January 1, 2020)

    date_obj = reference + timedelta(days=int_to_convert)

    return date_obj


def get_dtm_values(parcel_os_code, app_config):
    """
    Query the DTM database based on longitude and latitude to retrieve
    elevation, slope and aspect data.
    The output of this function is a dictionary with the following keys:
    'x', 'y', 'elevation', 'slope', 'aspect'
    """
    # pylint: disable=R0914
    db_name = app_config.dem_parameters["db_name"]
    db_user = app_config.dem_parameters["username"]
    db_password = app_config.dem_parameters["password"]

    conn = None

    # retrieve lon, lat from parcel_os_code and create a bounding box to
    # find the closest 50m grid cell in the DEM
    lon, lat = osgrid2lonlat(parcel_os_code)
    lon_min, lon_max, lat_min, lat_max = lon - 50, lon + 50, lat - 50, lat + 50
    try:
        conn = psycopg2.connect(
            user=db_user,
            password=db_password,
            database=db_name,
            host="127.0.0.1",
            port="5432",
        )
        conn.autocommit = True
        cur = conn.cursor()
        sql = f"""
            SELECT terrain.x, terrain.y, terrain.val, terrain.slope, terrain.aspect
            FROM dtm.dtm_slope_aspect AS terrain
            WHERE terrain.x BETWEEN {lon_min} AND {lon_max}
            AND terrain.y BETWEEN {lat_min} AND {lat_max};
        """
        cur.execute(sql)
        sql_return = cur.fetchall()
        lon_lst = [x[0] for x in sql_return]
        lat_lst = [x[1] for x in sql_return]
        closest_lon, closest_lat = nearest(lon, lon_lst), nearest(lat, lat_lst)
        ind = [
            i for i, x in enumerate(sql_return) if x[0:2] == (closest_lon, closest_lat)
        ]
        dtm_vals = sql_return[ind[0]]
        dict_keys = ["x", "y", "elevation", "slope", "aspect"]
        dtm_dict = dtm_dict = dict(zip(dict_keys, dtm_vals))
        return dtm_dict
    except psycopg2.DatabaseError as error:
        print(error)
        return None
    finally:
        if conn is not None:
            conn.close()


def find_contiguous_sets(data_frame, col_name):
    """
    Returns ordinal indices of contiguous non-NA values in
    a column of a dataframe that contains NAs and non-NA
    values.
    ------------------------------------------------------

    input arguments:
    :param data_frame: the pandas dataframe to query
    :param col_name: the column of the dataframe for which
        indices must be computed.

    Output:
    a list of indices

    Example:
    df["col"] = [
        NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,
        1,2,3,4,5,6,7,8,7,6,7,8,9,
        NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,
        1,2,3,4,3,4,3,2,3,4,5,6,7,8,1,2,3,
        NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN,NaN
    ]

    >>> find_contiguous_sets(df, col)
    [
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        1,1,1,1,1,1,1,1,1,1,1,1,1,
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,
        0,0,0,0,0,0,0,0,0,0,0,0
    ]
    """
    pd_input = pd.DataFrame(
        {"value": data_frame[col_name], "tag": data_frame[col_name] >= 0}
    )

    first = pd_input.index[pd_input["tag"] & ~pd_input["tag"].shift(1).fillna(False)]
    last = (
        pd_input.index[pd_input["tag"] & ~pd_input["tag"].shift(-1).fillna(False)] + 1
    )
    tuple_list = list(zip(first, last))
    max_index = max(end for _, end in tuple_list)
    result = [0] * max_index
    for index, (start, end) in enumerate(tuple_list, start=1):
        for i in range(start, end):
            result[i] = index
    return result
