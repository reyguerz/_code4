__author__ = 'Rey Guerrero'

#***** Microgrid Model

# import python modules
import sys
import os
import math
import copy
from collections import deque

# import user defined modules
import VarList
import Component
import InverterEff # delete, not needed here
import AdminFunctions # may not be needed here if no more debugging and scenario generation is on a different module


#Constraints and Penalty Values
LoadMetFractionLimit = VarList.LoadMetFractionLimit
BatSOCRequiredMin = VarList.BatSOCRequiredMin
ECOEPenalty1 = VarList.ECOEPenalty1 # Load Met Fraction one month
ECOEPenalty2 = VarList.ECOEPenalty2 # Load Met Fraction one year
ECOEPenalty3 = VarList.ECOEPenalty3 # BatSOC Required Min one year

# need to check and be consistent with the ratings in the Component.py
PVunitcost = VarList.PVunitcost				#USD / kWp
PVAnnualPercent = VarList.PVAnnualPercent		# annual O&M as percent of initial investment
WTunitcost = VarList.WTunitcost					# USD / kW
WTAnnualPercent = VarList.WTAnnualPercent 		# annual O&M as percent of initial investment
Batunitcost = VarList.Batunitcost				# USD / kWh
BatAnnualcost = VarList.BatAnnualcost			# annual O&M as percent of initial investment
Inverterunitcost =  VarList.Inverterunitcost	#USD/kWh


# ****************FUNCTION DEFINITION: ACTUAL SIMULATION


def Simulation(OneScenario,Sizes):

	#Meteorological and Load Data.

	Irradiance = OneScenario[0]
	WindSpeed = OneScenario[1]
	Temp = OneScenario[2]
	Demand = OneScenario[3]

	# error checking for the scenarios...
	TimeSteps = 0
	if (len(Irradiance) == len(WindSpeed)) & (len(WindSpeed) == len(Demand)) & (len(Demand) == len(Temp) - 1):
		TimeSteps = len(Irradiance)
	else:
		print('ERROR in input data. duration mismatch')
		rowError = 'ERROR in input data. duration mismatch'



	# Design Sizes
	PVSize = Sizes[0]	# check components for unit size
	WTSize = Sizes[1]	# check components and WT LUT code for unit size
	BatSize = Sizes[2] 	# check components and code below for unit size
	#!! IMPORTANT: CHECK INVERTER EFF CODE AND SPECS


	# Other variables to initialize for the loop / project life simulation
	DeltaDemandServed = []
	PExcess = []
	BatSOC = 0
	PeakValleyIndex = []
	Temp4Bat = 0
	BatteryReplacement = 1
	InverterReplacement = 0

	BatChargeRated = BatSize * 1000 # Wh
	BatChargeRemainingCap = BatChargeRated
	BatMaxSOCcriteria = 1
	BatChargeStatMaxSOC = BatMaxSOCcriteria * BatChargeRated # Wh
	BatChargeStatMinSOC = VarList.BATminSOC * BatSize *1000 # Wh
	BatChargeStat =  BatSize * 1000 # Wh, start at full charge
	BatSOH = 1 
	BatStartTime = -2	# code dependent value. variable needed to restart cycle and SOC count when battery is replaced
	minBatSOH = VarList.minBatSOH		#criteria when to change the battery
	BatChEff = VarList.BatChEff
	BatDisChEff = VarList.BatDisChEff
	minBatSOC = 1 # initial value

	#Battery parameters for degradation computation
	BatSOC = BatChargeStat / BatChargeRemainingCap	# initial SOC, to be used for battery degradation comp
	BatSOCAve = BatSOC # initial average
	Temp4Bat = Temp[0]
	Temp4BatAve = Temp4Bat # initial average = to initial temperature
	BatTime = 0 # 0 at initial SOC and temperature
	BatDegCycling = 0
	RainFlowBuffer = deque()
	PrevRFB = deque()
	PeakValley = []
	PrevPair = 0

	CumDegCycFix = 0

	TotalDemandServed = 0
	TotalRequiredLoad = 0
	SimulationBreak = 0


	



	for i in range (TimeSteps): # for i in range (1,TimeSteps + 1): # i = 0 is initial value
		
		if (i % 50000 == 0):
			print(i, 'of ',TimeSteps, ' TimeSteps/Hours')
		#*** Initialization / Update for each time step, consider degradation

		Component.TimeIndex = i
		Component.AmbientTemp = Temp[i+1]	#additional one timestep since temp at time = 0 (or i = -1) is also stored for battery degradation comp
		Component.PVIrradiance = Irradiance[i]
		Component.PVSize = PVSize
		PSolar = Component.SolarPVOut()
		
		Component.WTWindSpeed = WindSpeed[i]
		Component.WindTBSize = WTSize
		Pwind = Component.WindTBOut()
		#print(i, ' Demand ', Demand[i])
		PToInverter = Component.Inverter(Demand[i]) # computes for the required input to the inverter given the load to satisfy
		#print(i, ' P2Inverter ', PToInverter)
		PGen = PSolar + Pwind
		
		#*** Dispatch Strategy

		if PGen >= PToInverter: # Generated power is greater than demand (plus inverter load effects)
			DeltaDemandServed.append(0) # Load Served = Demand , 	#!!! CAN STILL BE OPTIMIZED: may not need to be saved every time slot 
			ForBatCharging = (PGen - PToInverter) / BatChEff
			if ForBatCharging <= BatChargeStatMaxSOC - BatChargeStat:
				BatChargeStat += ForBatCharging	# update battery charge state	
				PExcess.append(0)									#!!! CAN STILL BE OPTIMIZED !!!#
						
			else: # ForBatCharging > BatChargeStatMaxSOC - BatChargeStat
				PExcess.append(ForBatCharging - (BatChargeStatMaxSOC - BatChargeStat))
				BatChargeStat = BatChargeStatMaxSOC # update battery charge state
				
		else: # Generated power is less than demand
			ForBatDischarging = (PToInverter - PGen) / BatDisChEff
			PExcess.append(0) 
			if ForBatDischarging <= BatChargeStat - BatChargeStatMinSOC: # check battery capacity
				DeltaDemandServed.append(0) # Load Served = Demand, battery can supply the energy deficit
				BatChargeStat -= ForBatDischarging  # reduce battery charge
				
			else: # not enough battery charge to supply demand
				#Update ActualLoad because of load effects on inverter
				#Updated Actual load served can only go down further because there is not enough generation and battery charge
				
				ActualLoadServed = Component.InverseInverter(PGen + (BatChargeStat - BatChargeStatMinSOC)*BatDisChEff)
				DeltaDemandServed.append(ActualLoadServed - Demand[i]) 
				# load served is lower than demand
				BatChargeStat = BatChargeStatMinSOC # update battery charge state
				

		


		#*** Update battery State of Health and Remaining Capacity considering degradation

		#* update degradation due to calendar aging
		# SOC moving average
		PrevBatSOC = BatSOC
		BatSOC = BatChargeStat / BatChargeRemainingCap
		
		BatSOCAve = (BatSOCAve * (BatTime + 1) + BatSOC) / ( BatTime + 2) # BatTime has "+ 1" because initial BatTime = 0

		Temp4Bat = Temp[i+1]
		Temp4BatAve = (Temp4BatAve * (BatTime + 1) + Temp4Bat) / (BatTime + 2)
		
		DegCalAging = Component.BatterySOHDegCalAging(BatSOCAve, Temp4BatAve, BatTime) # BatTime has no "+ 1" because assume 100% Health on the first time step

		BatTime += 1 # for battery degradation computation at the next time step

		#* update degradation due to cycling aging

		ReversalFound = 0
		if (i >= 1) & (BatTime > 1):
			CheckPair = BatSOC - PrevBatSOC
			if PrevPair * CheckPair < 0: # then reversal
				ReversalFound = 1
				PrevPair = CheckPair
			elif CheckPair != 0:
				PrevPair = CheckPair
		else:
			#print('this hshould he executed')
			PrevPair = BatSOC - PrevBatSOC
			if i == 0:
				RainFlowBuffer.append([0, PrevBatSOC, Temp[0]]) # first entry to Rain Flow BUffer
				PrevRFB = copy.deepcopy(RainFlowBuffer)



		RainFlowBuffer = copy.deepcopy(PrevRFB) # revert back to RFB, last PeakValley
		DegCycFix = 0
		DegCycVar1 = 0
		DegCycVar2 = 0

		if (ReversalFound == 1):

			# add PeakValley to RainFlow Buffer
			PeakValley = [i, PrevBatSOC, Temp[i]]
				#print('Reverasal at',PeakValley)
			RainFlowBuffer.append(PeakValley) # add peak or valley
				#PrevRFB = copy.deepcopy(RainFlowBuffer) # "save" peakvalley, last
			# compute cycles and degradation with the addtion of the PeakValley
			# these are for full and "legit" half cycles
			# RainFlowBuffer will be modified, removing these cycles
			# degradation due to these cycles are fixed and saved in DegCycFix
			# note that RainFlowBUffer will not be modified if it's length is < 3
			DegCycFix = Component.RainFlowCount(RainFlowBuffer)
			

			#print(i,' RFB remaining: ', len(RainFlowBuffer))
			

			PrevRFB = copy.deepcopy(RainFlowBuffer)
			#print('Dcyc Fix:', DegCycFix)
			# succeeding computation are "temporary" or based on the new point/SOC that may not be a PeakValley
			# add new pint
			if BatSOC != RainFlowBuffer[-1][1]:
				RainFlowBuffer.append([i + 1, BatSOC, Temp[i+1]]) # add latest point			 
			#print('RFB lenght: ',len(RainFlowBuffer))
			DegCycVar1 = Component.RainFlowCount(RainFlowBuffer) # RainFlowBuffer may be modified
			DegCycVar2 = Component.RFB2HalfCycles(RainFlowBuffer) # returns zero if length is less than 2
		else:
			# not a reversal
			if BatSOC != RainFlowBuffer[-1][1]:
				RainFlowBuffer.append([i+1, BatSOC, Temp[i+1]])
			#print('RFB length = ',len(RainFlowBuffer))
			DegCycVar1 = Component.RainFlowCount(RainFlowBuffer)
			DegCycVar2 = Component.RFB2HalfCycles(RainFlowBuffer)

		CumDegCycFix += DegCycFix
		BatDegCycling = CumDegCycFix + DegCycVar1 + DegCycVar2

		BatSOH = Component.BatterySOHUpdate(DegCalAging + BatDegCycling)
		#print(CumDegCycFix, ' ', DegCycVar1, ' ',DegCycVar2)

		
		if BatSOH > minBatSOH: # update remaining capacity and charge at maxSOC
			BatChargeRemainingCap = BatChargeRated * BatSOH 	#double check
			BatChargeStatMaxSOC = BatMaxSOCcriteria * BatChargeRemainingCap 
		else:	# replace battery
			BatChargeRemainingCap = BatChargeRated
			BatChargeStatMaxSOC = BatMaxSOCcriteria * BatChargeRemainingCap
			BatteryReplacement += 1
			BatSOC = BatChargeStat / BatChargeRemainingCap	# initial SOC, to be used for battery degradation comp
			Temp4BatAve = Temp[i+1]
			BatTime = 0
			BatDegCycling = 0
			RainFlowBuffer = deque()
			RainFlowBuffer.append([i,BatSOC,Temp[i+1]])
			PrevRFB = deque()
			PrevRFB = copy.deepcopy(RainFlowBuffer)

		
		if BatChargeStat > BatChargeRemainingCap:
			BatChargeStat = BatChargeRemainingCap	# actual charge lost because of degradation when battery is fully charged

		
		#*** Compute Demand Served and Reliability Metric
		TotalRequiredLoad += Demand[i]
		TotalDemandServed += Demand[i] + DeltaDemandServed[i]
		

		if BatSOC < minBatSOC:
			minBatSOC = BatSOC

		if i == (30 * 24 - 1) : # one month check
			LoadMetFraction = TotalDemandServed / TotalRequiredLoad
			if LoadMetFraction  < LoadMetFractionLimit:
				ECOE = ECOEPenalty1
				SimulationBreak = 1
				break
		elif i == (365 * 24 - 1): # one year check
			LoadMetFraction = TotalDemandServed / TotalRequiredLoad
			if LoadMetFraction  < LoadMetFractionLimit:
				ECOE = ECOEPenalty2
				SimulationBreak = 1
				break
			
			if minBatSOC >= BatSOCRequiredMin :
				ECOE = ECOEPenalty3
				SimulationBreak = 1
				break
		
	

	#*** Cost model
	#PV
	InitInv = PVSize * PVunitcost *(Component.PVatSTC / 1000)	#asssuming per kW costing
	Annual = InitInv * PVAnnualPercent * (TimeSteps / (365*24))	# assuming per hour simulation 
	CostPV = InitInv + Annual

	#WindTB
	InitInv = WTSize * WTunitcost *(Component.WindTBLUTMax / 1000) #asssuming per kW costing
	Annual = InitInv * WTAnnualPercent * (TimeSteps / (365*24)) #assuming per hour simulation
	CostWT = InitInv + Annual

	# Inverter Costing
	InvBufferSize = VarList.InvBufferSize	#higher than the max Deman
	InvSize = math.ceil(InvBufferSize*Component.InvRatedPower/1000)
	InitInv = InvSize * Inverterunitcost				# inverter cost is USD/kw
	YearstoReplace = VarList.YearstoReplace
	Replacements = math.ceil(TimeSteps / (24*365*YearstoReplace))
	CostInv = InitInv * Replacements

	#Battery Costing
	InitInv = BatSize * Batunitcost #* (BatChargeRated / 1000)
	Annual = InitInv * BatAnnualcost * (TimeSteps/(365*24))
	CostBat = InitInv * BatteryReplacement + Annual

	TotalCost = CostPV + CostWT + CostInv + CostBat

	if SimulationBreak == 0:
		ECOE = (TotalCost / (TotalDemandServed/1000)) 	# in USD/kWh
	
	metrics = []
	metrics.append(ECOE)
	metrics.append(TotalCost)
	metrics.append(TotalDemandServed)

	return metrics


#************************ END:  FUNCTION DEFINITION/SIMULATION


#ECOE = Simulation()
#print(ECOE)


