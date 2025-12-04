[![macOS, Windows and Ubuntu CI/CD](https://github.com/mcmancini/UkWofost/actions/workflows/ci_workflow.yml/badge.svg)](https://github.com/mcmancini/UkWofost/actions/workflows/ci_workflow.yml)

# UK WOFOST

UK specific implementation of the [`WOFOST`](https://www.wur.nl/en/research-results/research-institutes/environmental-research/facilities-tools/software-models-and-databases/wofost.htm) crop yield simulation model in order to estimate future crop yields at the parcel level for the UK based on [`Mesoclim UKCP18 downscaled climate projections`](https://github.com/ilyamaclean/mesoclim) at parcel (field) level. Underlying soil data required to run the crop yield model come from [`SoilGrids`](https://www.isric.org/explore/soilgrids) or from the [`World Harmonized Soil Database`](https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/harmonized-world-soil-database-v12/en/) from FAO.  

## Authors, affiliation and licence

**Mattia Mancini**: Land, Environment, Economics and Policy Institute (LEEP), University of Exeter, Exeter EX4 4PU, United Kingdom. Email: <m.c.mancini@exeter.ac.uk>  
This work is licensed under

## Content

- [Setup](#setup)
    - [Pre-requisites](#pre-requisites)
        - [Pre-requisites for local install](#pre-requisites-for-local-install)
        - [Pre-requisites for API](#pre-requisites-for-api)
    - [Local installation](#local-installation)
    - [API](#api)
- [Usage](#usage)
    - [Usage of WOFOST from local install](#usage-of-wofost-from-local-install)
    - [Usage of the API](#usage-of-the-api)
- [Details](#overview)
    - [Modules](#modules)
    - [Types](#types)

## Setup

### Pre-requisites
There are two ways to run the UK implementation of the WOFOST crop yield model:  
1. Locally  
2. Making a call to an API  

The first option is the better option if you want a local copy of the UK implementation of WOFOST 8.0 but requires significant disk space for data storage and time for data preparation; the second option is only available if you are member of the University of Exeter and are connected to the University network through a VPN but is the best option for testing and to run experiments; it is also currently maintained.

The sections below will list the pre-requisites to install a local copy of the UK implementation of the WOFOST 8.0 crop yield model:

#### Pre-requisites for local install
- A [`Python`](https://www.python.org/) installation (3.11+).
- [`Conda`](https://docs.conda.io/en/latest/), a packaging and dependency manager.
- **Data**: this includes the following:  
    1. **Weather data**: this consists of parcel-level csv files each containing daily weather observations/predictions for the timeframe of interest. 
    2. **Crop data**: this consists of yaml files containing crop-specific parameters. These files are available in the [resources folder](resources\CropData) of the repository and are slightly modified versions of the crop files available in the original [Wofost implementation from Wageningen](https://github.com/ajwdewit/WOFOST_crop_parameters/tree/wofost80).
    3. **Soil data**: This can be downloaded, pre-processed and stored using the [`bulk_soilgrid_downloader.py](ukwofost\utility\bulk_soilgrids_downloader.py) script.
    4. **Management data**: this is a yaml file that defines standard management practices in the UK for the most commonly grown crops; a copy is stored in the [ManagementData folder](resources\ManagementData\crop_management.yaml)
    5. **Land parcel data**: this is contained in a PostgreSQL database and contains the shapefiles of all land parcels in the UK, as well as a 50m resolution DTM  
        

#### Pre-requisites for API
You will need the following:  
- Any software that allows to make API calls and build payloads such as R or Python;

### Local Installation
This section will cover how to install a local version of the UK implementation of the WOFOST 8.0 crop yield model.  
The following steps are required:  
1. First, make sure you have all the required data saved locally;
2. Clone the UkWofost repository to your local machine;
3. Open a Conda terminal, navigate to your local UkWofost folder and then create a new Conda environment from file with the following command: `conda env create -f wofost-env.yml`. This will create a new environment called `wofost` containing all the necessary python packages.
4. Once the environment is created, activate it: `conda activate wofost`.
5. Open your preferred IDE (for example Visual Studio Code) making sure to set the python interpreter to point to the wofost conda environment. In VSC this is done easily directly from the Conda terminal: once the wofost environment is active, just type in the Conda terminal `code`. This will open a new VSC window with the active wofost environment.
6. Create a copy of the [`config.ini.example`](config.ini.example) configuration file, to be named `config.ini`. Open it and modify the content to point to the correct data locations and PostgreSQL database. Save the new file in the main project directory (the same where the `config.ini.example` file is stored). 
The local installation is now complete.

### API
No installation is required if using the API.

## Usage

### Usage of WOFOST from local install
The [examples](examples) folder contains a Jupiter notebook named [wofost_local_run.ipynb](examples\wofost_local_run.ipynb) which illustrates in detail how to run a local instance of the UK implementation of the Wofost 8.0 model.

### Usage of the API
The [examples](examples) folder contains a Jupiter notebook named [wofost_api.ipynb](examples\wofost_api.ipynb) which illustrates in detail how to run instances of the UK implementation of the WOFOST crop yield model using the API

## Details

### Modules

### Types
