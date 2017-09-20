__author__ = 'Rey Guerrero'

#***** Parameters and Model of Components

#**

import os
import sys
import math
from collections import deque
import random

import VarList # import user-defined parameters 

#** import look up tables
import WindTBWvsP
import InverterEff
import PVDeg
import WindTBDeg


#** "Global" variables that may be used by two or more functions
TimeIndex = 0		# initial value only. this pertains to the time in the project life simulation. Primarily used for degradation computation
AmbientTemp = 1		# Kelvin, initial value only. values to be updated by the simulation
Temperature = []	# all temperature at given time index, for battery degradation

#** Solar Photovoltaic Model and Paramaters, 

PVIrradiance = 0 					#initial value only. values to be updated by the simulation
PVSize = 0							#initial value only. values to be updated by the simulation
PVatSTC = VarList.PVatSTC			# unit
PVTempCoeff = VarList.PVTempCoeff
PVTemp = 1							#initial value only. to be computed during the simulation
NOCT = VarList.NOCT					# Celsius
PVEff = VarList.PVEff				#BOS efficiency loss
PVDegLUT = PVDeg.LUT				#degradation look up table


def SolarPVOut(): # computation for temperature is in terms of Celsius
	indextime = math.floor(TimeIndex / 24)		# divide by 24, assuming TimeIndex is per hour and degradation values change every day
	PVTemp = (AmbientTemp - 273) + (NOCT - 20) * (PVIrradiance/800)
	powerout = PVDegLUT[indextime] * PVSize * PVEff *(PVIrradiance/1000)*PVatSTC*((PVTemp - 25)*PVTempCoeff + 1 )

	return powerout


#*** Search Method

def SearchLUTBisectionMethod(LUTContent, LUT): 
	maxindex = len(LUT)-1
	minindex = 0
	index = random.randrange(len(LUT))
	direction = 2
	Loop = 1
	SearchResult = []

	while Loop == 1:
		if LUTContent < LUT[index]:
			maxindex = index
		elif LUTContent > LUT[index]:
			minindex = index
		else:
			direction = 0
			Loop = 0
			break

		if (maxindex - minindex == 1):
			if index == maxindex:
				direction = -1
			elif index == minindex:
				direction = 1
			Loop = 0
		else:
			index = round((maxindex + minindex)/2)
			direction = 0


	SearchResult.append(index)
	SearchResult.append(direction)

	return SearchResult


#** Wind Turbine Model and Parameters

WTWindSpeed = 0			# initial value only. to be updated during the simulation
WindTBSize = 1			# initial value only. to be updated during the simulation
WindTBLUTMax = WindTBSize * WindTBWvsP.WindTBPowerRating
WindTBLUTW = WindTBWvsP.LUTWindSpeed
WindTBLUTP = WindTBWvsP.LUTPout

def WindTBOut():
	SearchResult = SearchLUTBisectionMethod(WTWindSpeed, WindTBLUTW)

	if SearchResult[1] != 0:
		a = int(SearchResult[0])
		b = int(SearchResult[0] + SearchResult[1])
		#linear interpolation
		m = (WindTBLUTP[b] - WindTBLUTP[a]) / ( WindTBLUTW[b] - WindTBLUTW[a]) # slope
		powerout = WindTBLUTP[a] + (WTWindSpeed - WindTBLUTW[a]) * m
		#print("a: ",a," b: ",b)
	else:
		#print(SearchResult[0])
		powerout = WindTBLUTP[int(SearchResult[0])]

	return powerout * WindTBSize


#*** Inverter Model and Parameters

InvRatedPower = VarList.InvRatedPower		#basically the max output power
#InverterEff.RatedPower = InvRatedPower
InvLUTPin = InverterEff.LUTPin
InvLUTPout = InverterEff.LUTPout


def Inverter(Demand):
	SearchResult = SearchLUTBisectionMethod(Demand, InvLUTPout)

	if SearchResult[1] != 0:
		a = int(SearchResult[0])
		b = int(SearchResult[0] + SearchResult[1])
		#linear interpolation
		m = (InvLUTPin[b] - InvLUTPin[a]) / ( InvLUTPout[b] - InvLUTPout[a]) # slope
		powerin = InvLUTPin[a] + (Demand - InvLUTPout[a]) * m
	else:
		powerin = InvLUTPin[int(SearchResult[0])]

	return powerin


def InverseInverter(PSupplied):
	SearchResult = SearchLUTBisectionMethod(PSupplied, InvLUTPin)

	if SearchResult[1] != 0:
		a = int(SearchResult[0])
		b = int(SearchResult[0] + SearchResult[1])
		#linear interpolation
		m = (InvLUTPout[b] - InvLUTPout[a]) / ( InvLUTPin[b] - InvLUTPin[a]) # slope
		powerout = InvLUTPout[a] + (PSupplied - InvLUTPin[a]) * m
		
	else:
		powerout = InvLUTPout[int(SearchResult[0])]

	return powerout




#*** Battery Model and Parameters
''' Battery Model input and output explanation

Required Input:
- Temperature --> Global variable. see above
- Temperature running average
- t index --> Global variable. see above
- SOC at all time steps (for computation of degradation due to cycling)
- SOC running average


Internal intermediate Variables:
-PeakValley
-DoD from rainflow
-SOC from rainflow
-cycle number from rainflow
-cycle begin and end time from rainflow (different end time for half or full cycle)

Required Output : SOH in Wh

'''

#Battery Input Variables
SOC = [] 		# initial/default value only. to be updated during simulation, MicrogridModel
Temp = []		# initial/default value only. to be updated during simulation, MicrogridModel


#Battery model coefficients
TempRef = VarList.TempRef
kTemp = VarList.kTemp
SOCRef = VarList.SOCRef
kSOC = VarList.kSOC
ktimestress = VarList.ktimestress	# assummed to be per second
kaDOD = VarList.kaDOD
kbDOD = VarList.kbDOD
kcDOD = VarList.kcDOD
kCrate = VarList.kCrate
Cref = VarList.Cref
pSEI = VarList.pSEI
rSEI = VarList.rSEI

def BatterySOHDegCalAging(BatSOCAve, Temp4BatAve, BatTime):
	#degradation due to calendar aging
	
	fT = (math.e)**( kTemp * (Temp4BatAve - TempRef) * (TempRef / Temp4BatAve))
	fSOC = (math.e) ** ( -1 * (SOCRef / BatSOCAve) * (((BatSOCAve - SOCRef)/kSOC)**2) )  
	dcal = (BatTime * 3600) * ktimestress * fSOC * fT	

	return dcal

def BatteryDegCycleCalc(Cycle,n): # n = 1 or 0.5 if full or half cycle

	dcyc = 0

	if len(Cycle) > 0:
		for i in range(len(Cycle)):
			DoD = math.fabs(Cycle[i][0][1] - Cycle[i][1][1]) 
			SoC = (Cycle[i][0][1] + Cycle[i][1][1]) / 2
			Temp1 = (Cycle[i][0][2] + Cycle[i][2][2]) / 2
			
			Crate = DoD * 2 * n  / (Cycle[i][2][0] - Cycle[i][0][0]) # !! Assuming Time index is per hour

			fDOD = (kaDOD * (DoD ** kbDOD) + kcDOD) ** (-1.0)
			fSOC = (math.e) ** ( -1 * (SOCRef / SoC) * (((SoC - SOCRef)/kSOC)**2) )
			fCrate = (math.e) ** (kCrate * (Crate - Cref))
			fTemp = (math.e)**( kTemp * (Temp1 - TempRef) * (TempRef / Temp1))
			fullhalfcycle = n
			dcyc += fDOD * fSOC * fCrate * fTemp * fullhalfcycle

	return dcyc

#** RainFlow Method specific for battery cycle computations

def RainFlowCount(RainFlowBuffer):

	CountedHalfFull = 0 # degradation
	RainFlowHalfCycle = []
	RainFlowFullCycle = []


	while len(RainFlowBuffer) >= 3:
		R1 = math.fabs(RainFlowBuffer[-2][1] - RainFlowBuffer[-3][1])
		R2 = math.fabs(RainFlowBuffer[-1][1] - RainFlowBuffer[-2][1])

		tstartend = []
		if (R1 < R2) & ( len(RainFlowBuffer) == 3): 
			
			tstartend.append(RainFlowBuffer[0]) # starting of cycle, referred by the time index
			tstartend.append(RainFlowBuffer[1]) # peak/valley of thed cycle, referred by the time index
			tstartend.append(RainFlowBuffer[1]) # ending of cycle, referred by the time index
			RainFlowHalfCycle.append(tstartend)
			tstartend = []
			RainFlowBuffer.popleft()

			break;
		elif R1 < R2:
			tstartend.append(RainFlowBuffer[-3]) # start of the cycle, referred by the time index
			tstartend.append(RainFlowBuffer[-2]) # peak or valley of the cycle, referred by the time index
			tstartend.append(RainFlowBuffer[-1]) # end of the cycle, referred by the time index
			RainFlowFullCycle.append(tstartend)
			tstartend = []
			# remove start and end points of R1 in the RainFlowBuffer
			last = RainFlowBuffer.pop()
			RainFlowBuffer.pop()
			RainFlowBuffer.pop()
			RainFlowBuffer.append(last)

		else:
			break 
	if RainFlowHalfCycle != []:
		CountedHalfFull = BatteryDegCycleCalc(RainFlowHalfCycle, 0.5) 
	if RainFlowFullCycle != []:
		CountedHalfFull += BatteryDegCycleCalc(RainFlowFullCycle, 1)


	return CountedHalfFull # Y


def RFB2HalfCycles(RainFlowBuffer):

	CountedHalf = 0 # degradation
	RainFlowHalfCycle = []


	if len(RainFlowBuffer) >= 2:
		for n in range (1,len(RainFlowBuffer)):
			tstartend = []
			tstartend.append(RainFlowBuffer[n-1]) 	# start of the cycle, referred by the time index
			tstartend.append(RainFlowBuffer[n]) 	# peak or valley of the cycle, referred by the time index
			tstartend.append(RainFlowBuffer[n])		# end of the cycle, referred by the time index
			RainFlowHalfCycle.append(tstartend)
	
		CountedHalf = BatteryDegCycleCalc(RainFlowHalfCycle,0.5)


	return CountedHalf


def BatterySOHUpdate(d):

	SOH = (1 - pSEI) * ((math.e)**(-1*d)) + pSEI * ((math.e)**(-1*d*rSEI))

	return SOH

