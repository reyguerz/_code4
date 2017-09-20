__author__ = 'Rey Guerrero'

#******** List of Parameters and Variables**********#
#####################################################

#*** NOTE of the Following Data and Their Structures:
''' 
**Data**		**Defined Where**			**Important Where**
Scenarios		Scenario Gen				Microgrid Model
Sizes			Optimization Algo (SA)		Microgrid Model
Metrics			Microgrid Model 			Objective Function, main
PDFResults		Monte Carlo					main, VarList
'''

#*****Input and Output Files*******




#*****Objective Function*******
PDFCriteria = 'mean'					# "mean", "P90", "P10", or "StdDev". See hard coded in Objective Function module
ObjectiveMetric = 4						# which column/ metric to optimize. See data structure for PDFResults below. columns are hard-coded in Monte Carlo module
'''
column	Data
0		Size[0] PV
1		Size[1] WT
2		Size[2] Storage
3		Scenario Identified/Index
4		ECOE
5
6
7

'''

#*****Microgrid Model*******

# Constraints and Penalty Values
LoadMetFractionLimit = 0.99
BatSOCRequiredMin = 0.95
ECOEPenalty1 = 10000001 # Load Met Fraction one month
ECOEPenalty2 = 10000002 # Load Met Fraction one year
ECOEPenalty3 = 10000003 # BatSOC Required Min one year

# Cost values, need to check and be consistent with the ratings in the Component.py
PVunitcost = 2420			#USD / kWp
PVAnnualPercent = 0.02125	# annual O&M as percent of initial investment
WTunitcost = 2500			# USD / kW
WTAnnualPercent = 0.02 		# annual O&M as percent of initial investment
Batunitcost = 830			# USD / kWh
BatAnnualcost = 0.02		# annual O&M as percent of initial investment
Inverterunitcost =  500		#USD/kWh

#Battery Component Specs and Parameters
BATminSOC = 0.2			# minimum battery SOC during discharge
minBatSOH = 0.8			# criteria when to change the battery
BatChEff = 0.90			# charging efficiency
BatDisChEff = 0.90		# discharging efficiency
#Battery model coefficients
TempRef = 298 		
kTemp = 0.0693
SOCRef = 0.5
kSOC = 0.5345
ktimestress = 3.4E-10	# assummed to be per second
kaDOD = 16215
kbDOD = -1.722
kcDOD = 8650
kCrate = 0.2374
Cref = 1.0
pSEI = 0.0296
rSEI = 150.24

# Inverter Component Specs and Parameters
InvBufferSize = 1.50	#higher than the max Deman
YearstoReplace = 5
InvRatedPower = 28000		#basically the max output power. this is used in the inverter efficiency look up table

# Solar Photovoltaic Model and Paramaters, 
PVatSTC = 1000			# unit
PVTempCoeff = -0.005		
NOCT = 45				# Celsius
PVEff = 0.90			#BOS efficiency loss
PVAnnualDeg = -0.008 		# yearly degradation, linear degradation


# Wind TB Model and Parameters
#### check Wind TB look up table: WindTBWvsP
WTAnnualDeg = -0.016 	# yearly degradation
