##########################################
##########################################
##### DATA DOWNLOAD FOR WOFOST SETUP #####
##########################################
##########################################

##############################
########## 1. Setup ##########
##############################

# --------------------- #
##### 1.1 Libraries #####
# --------------------- #

library(ssh)

# ----------------------- #
##### 1.2 Directories #####
# ----------------------- #

wofost_dir <- "D:/jdd215/Data/PCSE-WOFOST/"
wofost_version <- "80" # MUST BE EITHER "80" OR "81"

# ------------------- #
##### 1.3 Parcels #####
# ------------------- #

parcels <- c(1652902, 5969854, 2007837, 5315941, 6155780, 3787634, 1994132, 927161, 2448843, 5011443, 1223633, 4999331, 5756123, 6575450, 4737102, 5520500, 254857, 6075848, 608837, 5289411, 1090199, 5394899, 6384863,
             1089359, 1770854, 775327, 593924, 248604, 176342, 6392565, 597204, 6240087, 5233348, 3180706, 6635613, 2716041, 345408, 2338196, 2752533, 6240087, 4966596, 1138219, 2916085, 6313721, 4386266, 6042963,
             43606, 4762467, 5935422, 1823506, 5756123, 3339486, 202549, 5967923, 1513437, 1994132, 4853136, 2338196, 1268149, 2465317) 

# --------------------- #
##### 1.4 Functions #####
# --------------------- #

create_dir <- function (dir) {
  if (!dir.exists(dir)) {
    dir.create(dir, recursive = TRUE)
  }
}

##############################################
########## 2. Create file structure ##########
##############################################

# ------------------- #
##### 2.1 Climate #####
# ------------------- #

create_dir(paste0(wofost_dir, "ClimateData/Mesoclim"))

# -------------------------------------- #
##### 2.2 Crop, Management, and Soil #####
# -------------------------------------- #

create_dir(paste0(wofost_dir, "Wofost_", wofost_version))
create_dir(paste0(wofost_dir, "Wofost_", wofost_version, "/SoilData"))


######################################
########## 3. Download Data ##########
######################################

# ----------------------------- #
##### 3.1 Connect to server #####
# ----------------------------- #

# Connect (this will ask for your password once in R)
session <- ssh_connect("jdaniels@mmlin.ex.ac.uk")

# ------------------------------------- #
##### 3.2 Download non-parcel files #####
# ------------------------------------- #

# a) Crop Data
scp_download(session,
             files = paste0("/media/mmancini/ssd/PCSE-WOFOST/Wofost_", wofost_version, "/CropData"),
             to = paste0(wofost_dir, "Wofost_", wofost_version, "/"))

# b) Management Data
scp_download(session,
             files = paste0("/media/mmancini/ssd/PCSE-WOFOST/Wofost_", wofost_version, "/ManagementData"),
             to = paste0(wofost_dir, "Wofost_", wofost_version, "/"))

# c) Soil Data
scp_download(session,
             files = paste0("/media/mmancini/ssd/PCSE-WOFOST/Wofost_", wofost_version, "/SoilData/GB_soil_data.nc"),
             to = paste0(wofost_dir, "Wofost_", wofost_version, "/SoilData/"))

# ------------------------------------------ #
##### 3.2 Download parcel-specific files #####
# ------------------------------------------ #

for (i in 1:length(parcels)) {
  
  parcel <- parcels[i]
  
  # a) Climate Data
  scp_download(session,
               files = paste0("/media/mmancini/ssd/PCSE-WOFOST/ClimateData/Mesoclim/parcel_", parcel, "_mesoclim.csv"),
               to = paste0(wofost_dir, "ClimateData/Mesoclim/"))

  # # b) Soil Data
  # scp_download(session,
  #              files = paste0("/media/mmancini/ssd/PCSE-WOFOST/Wofost_", wofost_version, "/SoilData/", parcel, ".bin"),
  #              to = paste0(wofost_dir, "Wofost_", wofost_version, "/SoilData/"))
}


ssh_disconnect(session)
