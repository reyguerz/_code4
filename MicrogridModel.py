__author__ = 'Rey Guerrero'

#***** Microgrid Model

import sys
import os
import math
import copy
from collections import deque
import Component
import InverterEff # delete, not needed here
import AdminFunctions # may not be needed here if no more debugging and scenario generation is on a different module
#import numba


from datetime import datetime
starttime = datetime.now()
rowError = 'No Run Time Error'

#Constraints and Penalty Values
LoadMetFractionLimit = 0.99
BatSOCRequiredMin = 0.95
ECOEPenalty1 = 10000001 # Load Met Fraction one month
ECOEPenalty2 = 10000002 # Load Met Fraction one year
ECOEPenalty3 = 10000003 # BatSOC Required Min one year

#************************ START: input variables and parameters
'''
TimeSteps = 4
Irradiance = [100,1000,1000,100]
WindSpeed = [0,10,0,15]
Temp = [303, 303,303,313,313]		# Kelvin, has one more data point at the start to indicate time = 0 temperature. this is to be used in the battery degradation comp
Demand = [505,700,100,700]
'''
Irradiance = []
WindSpeed = []
Temp = []
Demand = []
TimeSteps = 0

'''
AdminFunctions.ReadListCSVFile('inSolar.csv', Irradiance)
AdminFunctions.ReadListCSVFile('inWindSpeed.csv', WindSpeed)
AdminFunctions.ReadListCSVFile('inTemp.csv', Temp)
AdminFunctions.ReadListCSVFile('inLoad.csv', Demand)
'''
# code for simple 20 yr simulation by repeating 1 year data 20x
Dummy = []
AdminFunctions.ReadListCSVFile('inSolar.csv', Dummy)
for i in range(20):
	Irradiance += Dummy

Dummy = []
AdminFunctions.ReadListCSVFile('inWindSpeed.csv', Dummy)
for i in range(20):
	WindSpeed += Dummy

Dummy = []
AdminFunctions.ReadListCSVFile('inTemp.csv', Dummy)
Temp += Dummy
Dummy.pop(0)
for i in range(19):
	Temp += Dummy
	
Dummy = []
AdminFunctions.ReadListCSVFile('inLoad.csv', Dummy)
for i in range(20):
	Demand += Dummy
'''
print('Irradiance len: ', len(Irradiance))
print('Windspeed Len: ', len(WindSpeed))
print('Demand len: ',len(Demand))
print('Temp lenL ',len(Temp))
'''

if (len(Irradiance) == len(WindSpeed)) & (len(WindSpeed) == len(Demand)) & (len(Demand) == len(Temp) - 1):
	TimeSteps = len(Irradiance)
else:
	print('ERROR in input data. duration mismatch')
	rowError = 'ERROR in input data. duration mismatch'


PVSize = 30	# check components for unit size
WTSize = 40	 # check components and WT LUT code for unit size
BatSize = 300 # check components and code below for unit size
#!! IMPORTANT: CHECK INVERTER EFF CODE AND SPECS


# need to check and be consistent with the ratings in the Component.py
PVunitcost = 2420			#USD / kWp
PVAnnualPercent = 0.02125	# annual O&M as percent of initial investment
WTunitcost = 2500			# USD / kW
WTAnnualPercent = 0.02 		# annual O&M as percent of initial investment
Batunitcost = 830			# USD / kWh
BatAnnualcost = 0.02		# annual O&M as percent of initial investment
Inverterunitcost =  500		#USD/kWh

#************************ END:  input variables and parameters


# ****************FUNCTION DEFINITION: ACTUAL SIMULATION

#@numba.jit#(nopython = True)
def Simulation():

	#Initialization for the loop / project life simulation
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
	BatChargeStatMinSOC = 0.2 * BatSize *1000 # Wh
	BatChargeStat =  BatSize * 1000 # Wh, start at full charge
	BatSOH = 1 
	BatStartTime = -2	# code dependent value. variable needed to restart cycle and SOC count when battery is replaced
	minBatSOH = 0.8		#criteria when to change the battery
	BatChEff = 0.90
	BatDisChEff = 0.90
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

	#**Testing Purposes Only
	'''
	SolarPVOutEveryTimeStep = []
	WintTBOutEveryTimeStep = []
	'''
	
	'''
	#output to CSV
	OutFileName = 'output.csv'
	outfile = open(OutFileName,'w')


	row = 'hour, PVGen, WTGen, PGen, BatChargeStat,BatRemCap, Bat SOH, PToInverter, DeltaDemand, PExcess\n'
	outfile.write(row)
	'''
	
	
	TotalDemandServed = 0
	TotalRequiredLoad = 0
	SimulationBreak = 0

	for i in range (TimeSteps): # for i in range (1,TimeSteps + 1): # i = 0 is initial value

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

		PToInverter = Component.Inverter(Demand[i]) # computes for the required input to the inverter given the load to satisfy

		PGen = PSolar + Pwind

		#*** Dispatch Strategy

		if PGen >= PToInverter: # Generated power is greater than demand (plus inverter load effects)
			DeltaDemandServed.append(0) # Load Served = Demand , 	#!!! CAN STILL BE OPTIMIZED: may not need to be saved every time slot 
			ForBatCharging = (PGen - PToInverter) / BatChEff
			if ForBatCharging <= BatChargeStatMaxSOC - BatChargeStat:
				BatChargeStat += ForBatCharging	# update battery charge state	
				PExcess.append(0)									#!!! CAN STILL BE OPTIMIZED !!!#
				#print('\nCase 1')		
			else: # ForBatCharging > BatChargeStatMaxSOC - BatChargeStat
				PExcess.append(ForBatCharging - (BatChargeStatMaxSOC - BatChargeStat))
				BatChargeStat = BatChargeStatMaxSOC # update battery charge state
				#print('\nCase 2')
		else: # Generated power is less than demand
			ForBatDischarging = (PToInverter - PGen) / BatDisChEff
			PExcess.append(0) 
			if ForBatDischarging <= BatChargeStat - BatChargeStatMinSOC: # check battery capacity
				DeltaDemandServed.append(0) # Load Served = Demand, battery can supply the energy deficit
				BatChargeStat -= ForBatDischarging  # reduce battery charge
				#print('\nCase 3')
			else: # not enough battery charge to supply demand
				#Update ActualLoad because of load effects on inverter
				#Updated Actual load served can only go down further because there is not enough generation and battery charge
				
				ActualLoadServed = Component.InverseInverter(PGen + (BatChargeStat - BatChargeStatMinSOC)*BatDisChEff)
				DeltaDemandServed.append(ActualLoadServed - Demand[i]) 
				# load served is lower than demand
				BatChargeStat = BatChargeStatMinSOC # update battery charge state
				#print('\nCase 4')

		


		#*** Update battery State of Health and Remaining Capacity considering degradation

		#* update degradation due to calendar aging
		# SOC moving average
		PrevBatSOC = BatSOC
		BatSOC = BatChargeStat / BatChargeRemainingCap
		#print(BatSOC)
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

		#print('RFB lenght:',len(RainFlowBuffer))
		
		#print('\n***RFB0',RainFlowBuffer[0])

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


		'''
		print('\n Battery Charge State:', BatChargeStat)
		print('\n Battery Charge Max SOC:', BatChargeStatMaxSOC)
		print('\n Battery Charge Min SOC:', BatChargeStatMinSOC)
		print('\n Battery SOH:', BatSOH)
		print('\n DeltaDemandServed',DeltaDemandServed)
		print('\n ExcessPower:', PExcess)
		print('\n Generated Power', PGen)
		print('\n Required Power to Inverter', PToInverter)
		print('\n Irradiance', Component.PVIrradiance)
		'''
		
		#*** Compute Demand Served and Reliabiility Metric
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
		


		'''
		row = ''
		row += str(i+1) + ','
		row += str(PSolar) + ','
		row += str(Pwind) + ','
		row += str(PGen) + ','
		row += str(BatChargeStat) + ','
		row += str(BatChargeRemainingCap) + ','
		row += str(BatSOH) + ','
		row += str(PToInverter) + ','
		row += str(DeltaDemandServed[i]) + ','
		row += str(PExcess[i]) + '\n'
		outfile.write(row)
		'''
		#print('Finished computation at Timestep = ',i)#, ':', BatSOC,BatSOH)
		

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
	InvBufferSize = 1.50	#higher than the max Deman
	InvSize = math.ceil((InvBufferSize*max(Demand)) / Component.InvRatedPower)
	InitInv = InvSize * Inverterunitcost
	YearstoReplace = 5
	Replacements = math.ceil(TimeSteps / (24*365*YearstoReplace))
	CostInv = InitInv * Replacements

	#Battery Costing
	InitInv = BatSize * Batunitcost #* (BatChargeRated / 1000)
	Annual = InitInv * BatAnnualcost * (TimeSteps/(365*24))
	CostBat = InitInv * BatteryReplacement + Annual

	TotalCost = CostPV + CostWT + CostInv + CostBat

	if SimulationBreak == 0:
		ECOE = (TotalCost / (TotalDemandServed/1000)) 	# in USD/kWh
	
	'''
	# print checkers
	print('PV Init: ', InitInv)
	print('PV O&M: ', Annual)
	print('PV Cost: ', CostPV)

	print('WT Init: ', InitInv)
	print('WT O&M: ', Annual)
	print('WT Cost: ', CostWT)

	print('Inverter Init: ', InitInv)
	print('Inverter Replacements: ', Replacements)
	print('Inverter Cost: ', CostInv)

	print('Bat Init: ', InitInv)
	print('Bat O&M: ', Annual)
	print('Battery Cost: ', CostBat)

	print('Total Cost: ',TotalCost)
	print('ECOE: ',ECOE)

	print('\n# of Batteries Used: ' + str(BatteryReplacement))

	outfile.close()
	'''

	
	stoptime = datetime.now()

	print ('runtime: ',stoptime - starttime)
	outfile2 = open('runtimeECOE.txt','w')
	row = 'runtime: ' + str(stoptime - starttime)
	row += '\nTotalCost (USD): ' + str(TotalCost)
	row += '\nTotalDemandServed (W): ' + str(TotalDemandServed)
	row += '\nECOE: ' + str(ECOE)
	row += '\n# of Batteries Used: ' + str(BatteryReplacement)
	row += '\n' + rowError
	outfile2.write(row)
	outfile2.close()
	
	return ECOE

#************************ END:  FUNCTION DEFINITION/SIMULATION


#ECOE = Simulation()
#print(ECOE)


