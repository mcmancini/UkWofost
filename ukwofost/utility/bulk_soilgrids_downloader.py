"""
SoilGrids data downloader.
==========================

Author: Mattia Mancini
Created: 24-April-2023
--------------------------

Script that downloads and stores soil data retrieved from the SoilGrids
dataset to be used as input to the UK implementation of the WOFOST crop
model.

Soilgrids is a system for global digital soil mapping that uses
state-of-the-art machine learning methods to map the spatial distribution
of soil properties across the globe. SoilGrids prediction models are
fitted using over 230 000 soil profile observations from the WoSIS
database and a series of environmental covariates. Covariates were
selected from a pool of over 400 environmental layers from Earth
observation derived products and other environmental information including
climate, land cover and terrain morphology. The outputs of SoilGrids are
global soil property maps at six standard depth intervals (according to
the GlobalSoilMap IUSS working group and its specifications) at a spatial
resolution of 250 meters.

The SoilGrids dataset can be found at https://www.isric.org/explore/soilgrids;
it was downloaded using the soilgrids 0.1.3 library
(https://pypi.org/project/soilgrids/)
Docs at https://www.isric.org/explore/soilgrids/faq-soilgrids and
https://maps.isric.org/

Soil data from SoilGrids requires
to be processed as follows:
    - 1. Compute depth weighted averages of all values: the raw data is
            reported by depth, but we want averages for 0-60cm.
    - 2. Rescale values based on the conversion factors reported at
            https://www.isric.org/explore/soilgrids/faq-soilgrids
    - 3. Calculate depth-weighted averages for the 0-60cm depth range.
            This is done to generate a single value per soil property
            that can be used as input to WOFOST 8.0.
    - 4. Store data in a NetCDF file.
"""

import time
import numpy as np
from pyproj import Transformer
from soilgrids import SoilGrids
import xarray as xr
from ukwofost.core import app_config

soil_dir = app_config.data_dirs["soil_dir"]


# Conversion functions
def div_ten(x):
    """division by ten conversion function."""
    return x / 10.0


def div_hundred(x):
    """division by hundred conversion function."""
    return x / 100.0


# Conversion by soil parameter
# (see https://www.isric.org/explore/soilgrids/faq-soilgrids)
obs_conversions = {
    "bdod": div_hundred,
    "cec": div_ten,
    "cfvo": div_ten,
    "clay": div_ten,
    "nitrogen": div_hundred,
    "phh2o": div_ten,
    "sand": div_ten,
    "silt": div_ten,
    "soc": div_ten,
    "ocd": div_ten,
    "ocs": div_ten,
}


transformer = Transformer.from_crs(4326, 27700, always_xy=True)
x1, y1 = transformer.transform(
    -2.547855, 54.00366
)  # centroid of Great Britain
west, east, south, north = x1 - 0.5e6, x1 + 0.5e6, y1 - 0.8e6, y1 + 0.8e6
transformer = Transformer.from_crs(27700, 4326, always_xy=True)
bl = transformer.transform(west, south)
br = transformer.transform(east, south)
tl = transformer.transform(west, north)
tr = transformer.transform(east, north)

soilvars = [
    "bdod",
    "cec",
    "cfvo",
    "clay",
    "nitrogen",
    "phh2o",
    "sand",
    "silt",
    "soc",
    "ocd",
    "ocs",
]
soil_depths = ["0-5", "5-15", "15-30", "30-60", "60-100", "100-200"]
soil_grids = SoilGrids()
COUNTER = 1
soil_data = xr.Dataset()

# pylint: disable=W0718
for var in soilvars:
    print(f"Processing variable {COUNTER} of {len(soilvars)}: '{var}'")
    soil_chunk = xr.Dataset()
    if var == "ocs":
        while (
            True
        ):  # required because the server sometimes returns a 500 error
            DEPTH = "0-30"
            try:
                soil_data[var] = soil_grids.get_coverage_data(
                    service_id=var,
                    coverage_id=f"{var}_{DEPTH}cm_mean",
                    west=bl[0],
                    south=bl[1],
                    east=br[0],
                    north=tr[1],
                    width=4000,
                    height=6400,
                    crs="urn:ogc:def:crs:EPSG::4326",
                    output=(soil_dir + "/tmp.tif"),
                )
                # conversion to conventional units
                func = obs_conversions[var]
                soil_data[var] = func(soil_data[var])
            except Exception:
                print("get_coverage_data failed. Retrying in 60 seconds...")
                time.sleep(60)
                continue
            break
    else:
        for depth in soil_depths:
            while True:
                try:
                    soil_chunk[depth] = soil_grids.get_coverage_data(
                        service_id=var,
                        coverage_id=f"{var}_{depth}cm_mean",
                        west=bl[0],
                        south=bl[1],
                        east=br[0],
                        north=tr[1],
                        width=4000,
                        height=6400,
                        crs="urn:ogc:def:crs:EPSG::4326",
                        output=(soil_dir + "/tmp.tif"),
                    )
                    # conversion to conventional units
                    func = obs_conversions[var]
                    soil_chunk[depth] = func(soil_chunk[depth])
                except Exception:
                    print(
                        "get_coverage_data failed. Retrying in 60 seconds..."
                    )
                    time.sleep(60)
                    continue
                break

        # soil_chunk.to_netcdf(data_dirs['soils_dir'] + f'soil_{var}.nc')
        # Weighted average of soil variables for depths up to 60cm
        weight_factor = {"0-5": 1, "5-15": 2, "15-30": 3, "30-60": 6}
        # empty array to store the weighted average. Can't be an empty object
        # (i.e. xr.DataArray()) because dimensions cannot change for in-place
        # operations
        soil_data[var] = soil_chunk[depth] * 0

        for key, factor in weight_factor.items():
            df = soil_chunk[key] * factor
            soil_data[var] += df
        soil_data[var] = soil_data[var] / 12
        soil_data[var] = soil_data[var].where(soil_data[var] != 0, np.nan)
        COUNTER += 1
        time.sleep(60)

soil_data.to_netcdf(soil_dir + "/GB_soil_data.nc")
# pylint: enable=W0718
