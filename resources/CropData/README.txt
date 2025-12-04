## CROP PARAMETER FILES
## ====================
##
## Author: Mattia C. Mancini
## Date: 11 February 2025
## -------------------------
##
## Most of the crop files have been downloaded from https://github.com/ajwdewit/WOFOST_crop_parameters
## 

## The following crops have been added, or modified and parametrized as follows:

	- Winter barley:
          ==============
		changed the crop "barley" in ajwdewit/WOFOST_crop_parameters with parameter values taken from Gilardelli et al. 2018 (https://www.sciencedirect.com/science/article/pii/S0304380017304453)
		Some adjustments needed to be made to ensure that FLTB + FOTB + FSTB would not exceed 1.(FOTB @ 1 = 0.99 instead of 1 because FLTB @ 1 = 0.01)
		Also, partitioning FOTB at DVS=0.82 with value 0 results in the code breaking: pcse.exceptions.PartitioningError: Error in partitioning!
			Checksum: 0.000525, FR: 0.106, FL: 0.134, FS: 0.866, FO: 0.001
		So replaced DVS=0.82 to DVS=0.85 to match the other partition tables. This fixes the problem
		Things to note: LAIEM does not exist in the WOFOST 8.0 version
		
		Some missing parameters related to nutrition needed to be added (taken from wheat) as follows: 
			
			Line 427 and below:
			-------------------
			RNUPTAKEMAX:
            		- 5.00
            		- Maximum rate of N uptake
            		- ['mass.mass-1']

			Line 475 and below:
			-------------------
			RPUPTAKEMAX:
            		- 5.00
            		- Maximum rate of P uptake
            		- ['mass.mass-1']

			line 523 and below:
			-------------------
			RKUPTAKEMAX:
            		- 5.00
            		- Maximum rate of K uptake
            		- ['mass.mass-1']
            		#
            		# IMPORT DVS RELATED TO N/P/K UPTAKE AND TRANSLOCATION
            		#
            		DVS_NPK_STOP:
            		- 1.30
            		- development stage above which no crop N/P/K uptake occurs
            		- ['-']
            		DVS_NPK_TRANSL:
            		- 0.80
            		- development stage above which N/P/K translocation to storage organs does occur
            		- ['-']

			Also added (again taken from wheat): lines 549 and following:
			NPK_TRANSLRT_FR:
            		- 0.50
            		- NPK translocation from roots as a fraction of total NPK amounts translocated from leaves and stems
            		- ['-']

	- Spring barley:
	  ==============
		This was the default crop, which did not work because of some missing parameters related to nutrition.
		As for Winter barley, added the following:

		Parameters related to nutrition needed to be added (taken from wheat) as follows: 
			Line 418 and below:
			-------------------
			RNUPTAKEMAX:
            		- 5.00
            		- Maximum rate of N uptake
            		- ['mass.mass-1']
			
			line 466 and below:
			-------------------
			RPUPTAKEMAX:
            		- 5.00
            		- Maximum rate of P uptake
            		- ['mass.mass-1']
			
			line 514 and below:
			-------------------
			RKUPTAKEMAX:
            		- 5.00
            		- Maximum rate of K uptake
            		- ['mass.mass-1']
            		#
            		# IMPORT DVS RELATED TO N/P/K UPTAKE AND TRANSLOCATION
            		#
            		DVS_NPK_STOP:
            		- 1.30
            		- development stage above which no crop N/P/K uptake occurs
            		- ['-']
            		DVS_NPK_TRANSL:
            		- 0.80
            		- development stage above which N/P/K translocation to storage organs does occur
            		- ['-']

			Also added (again taken from wheat): lines 540 and following:
			NPK_TRANSLRT_FR:
            		- 0.50
            		- NPK translocation from roots as a fraction of total NPK amounts translocated from leaves and stems
            		- ['-']

	- Spring Wheat
	  ============
		Modified hte winter wheat crop parameter to follow the parametrisation from Li et al 2023 (https://pdfs.semanticscholar.org/b892/5806fa9fb61fa3f6dd68f492c3d178547b54.pdf)
		As I am not entirely convinced about what they did (in particular vernalisation and TSUMS!), I also made the following changes following the file for spring wheat
		available at https://pcse.readthedocs.io/en/stable/_downloads/54f76ee5cd7370528f9711110d0fd4dc/quickstart_part3.zip:
		TSUM1 = 800.
		TSUM2 = 1030.
		IDSL = 0

		Is it worthwhile to check whether we can translate the
		spring wheat file above for the LINTUL model to work in WOFOST maybe taking the parameters not included from winter wheat?

	- Spring oats
	  ===========
		Modified Spring Barley variety 301, following Greschkowiak 2020
		(https://www.researchgate.net/publication/351941487_Prospects_for_oat_production_under_a_changing_climate_in_Finland)
		Also needed to add the following for simulating nutrition:
		
		Line 418 and following:
		-----------------------
		RNUPTAKEMAX:
            	- 5.00
            	- Maximum rate of N uptake
            	- ['mass.mass-1']

		Line 466 and following:
		-----------------------
		RPUPTAKEMAX:
            	- 5.00
            	- Maximum rate of P uptake
            	- ['mass.mass-1']

		Line 514 and following:
		-----------------------
		RKUPTAKEMAX:
            	- 5.00
            	- Maximum rate of P uptake
            	- ['mass.mass-1']
		#
            	# IMPORT DVS RELATED TO N/P/K UPTAKE AND TRANSLOCATION
            	#
            	DVS_NPK_STOP:
            	- 1.30
            	- development stage above which no crop N/P/K uptake occurs
            	- ['-']
            	DVS_NPK_TRANSL:
            	- 0.80
            	- development stage above which N/P/K translocation to storage organs does occur
            	- ['-']

		Line 548 and following:
		-----------------------
            	NPK_TRANSLRT_FR:
            	- 0.50
            	- NPK translocation from roots as a fraction of total NPK amounts translocated from leaves and stems
            	- ['-']		
		
	- Winter oats
	  ===========
		This is most definitely a placeholder.
		I took spring barley from above, changed vernalisation requirements (IDSL = 2) and that's all. I could not find any reference to change TSUM1 and TSUM2 to different values. 
		Also needed to add the following for simulating nutrition:
		
		Line 418 and following:
		-----------------------
		RNUPTAKEMAX:
            	- 5.00
            	- Maximum rate of N uptake
            	- ['mass.mass-1']

		Line 466 and following:
		-----------------------
		RPUPTAKEMAX:
            	- 5.00
            	- Maximum rate of P uptake
            	- ['mass.mass-1']

		Line 514 and following:
		-----------------------
		RKUPTAKEMAX:
            	- 5.00
            	- Maximum rate of P uptake
            	- ['mass.mass-1']
		#
            	# IMPORT DVS RELATED TO N/P/K UPTAKE AND TRANSLOCATION
            	#
            	DVS_NPK_STOP:
            	- 1.30
            	- development stage above which no crop N/P/K uptake occurs
            	- ['-']
            	DVS_NPK_TRANSL:
            	- 0.80
            	- development stage above which N/P/K translocation to storage organs does occur
            	- ['-']

		Line 548 and following:
		-----------------------
            	NPK_TRANSLRT_FR:
            	- 0.50
            	- NPK translocation from roots as a fraction of total NPK amounts translocated from leaves and stems
            	- ['-']


	- Faba Beans
	  ==========
		Used the regular WOFOST parametrisation

	- Field peas
	  ==========
		NOT AVAILABLE and could not find anything from the literature


## ===================================
## NOTE: most crops parametrisations found online will not include nutrient parameters. This is because they were calibrated prior to the introduction of WOFOST 8.0 Beta which we are using and has been deprecated.