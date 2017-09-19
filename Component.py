__author__ = 'Rey Guerrero'

#***** Parameters and Model of Components

#**

import os
import sys
import math
from collections import deque
import random
#import numba

#** import look up tables
import WindTBWvsP
import InverterEff
import PVDeg
import WindTBDeg


#** "Global" variables that may be used by two or more functions
TimeIndex = 0			# initial value only. this pertains to the time in the project life simulation. Primarily used for degradation computation
AmbientTemp = 1		# Kelvin, initial value only. values to be updated by the simulation
Temperature = []	# all temperature at given time index, for battery degradation

#** Solar Photovoltaic Model and Paramaters, 

PVIrradiance = 0 		#initial value only. values to be updated by the simulation
PVSize = 0				#initial value only. values to be updated by the simulation
PVatSTC = 1000			# unit
PVTempCoeff = -0.005
PVTemp = 1				
NOCT = 45				# Celsius
PVEff = 0.90			#BOS efficiency loss
PVDegLUT = PVDeg.LUT	#degradation look up table

#@numba.jit#(nopython = True)
def SolarPVOut(): # computation for temperature is in terms of Celsius
	indextime = math.floor(TimeIndex / 24)		# divide by 24, assuming TimeIndex is per hour and degradation values change every day
	PVTemp = (AmbientTemp - 273) + (NOCT - 20) * (PVIrradiance/800)
	powerout = PVDegLUT[indextime] * PVSize * PVEff *(PVIrradiance/1000)*PVatSTC*((PVTemp - 25)*PVTempCoeff + 1 )

	return powerout


#*** Search Method

def SearchLUTBisectionMethod(LUTContent, LUT): # error when using numba.jit, need to edit code(?)
	maxindex = len(LUT)-1
	minindex = 0
	index = random.randrange(len(LUT))
	direction = 2
	Loop = 1
	SearchResult = []
	#print(maxindex, index, minindex)
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

	#	print(maxindex, index, minindex)
	#	nexti = input()

	SearchResult.append(index)
	SearchResult.append(direction)

	return SearchResult

#** Wind Turbine Model and Parameters

WTWindSpeed = 0
WindTBSize = 1
WindTBLUTMax = WindTBSize * WindTBWvsP.WindTBPowerRating
WindTBLUTW = WindTBWvsP.LUTWindSpeed
WindTBLUTP = WindTBWvsP.LUTPout

#@numba.jit#(nopython = True)
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

'''
#assuming uniform interval

WindTBLUT = WindTBWvsP.LUT
WindTBDegLUT = WindTBDeg.LUT
WindTBLUTMin = WindTBWvsP.MinWindSpeed
WindTBLUTMax = WindTBWvsP.MaxWindSpeed
WindTBLUTStep = WindTBWvsP.WindSpeedStep
WindTBLUTTotalSteps = 1 + (WindTBLUTMax - WindTBLUTMin)/WindTBLUTStep
WindTBRating = WindTBWvsP.WindTBPowerRating

def WindTBOut(): # assuming uniform interval
	indexdummy = (WindTBLUTTotalSteps - 1) * ((WTWindSpeed - WindTBLUTMin) / (WindTBLUTMax - WindTBLUTMin))
	indexlow = math.floor(indexdummy)
	indexhigh = math.ceil(indexdummy)
	indextime = math.floor(TimeIndex / 24)
	if indexlow == indexhigh:
		powerout = WindTBDegLUT[indextime] * WindTBLUT[int(indexdummy)]
	else: # linear interpolation
		powerout = WindTBDegLUT[indextime] * WindTBLUT[indexlow] + (indexdummy - indexlow) * (WindTBLUT[indexhigh] - WindTBLUT[indexlow])
	
	return (powerout * WindTBSize)
'''


#*** Inverter Model and Parameters

InvRatedPower = 28000
InverterEff.RatedPower = InvRatedPower
import InverterEff
InvLUTPin = InverterEff.LUTPin
InvLUTPout = InverterEff.LUTPout

#@numba.jit#(nopython = True)
def Inverter(Demand):
	SearchResult = SearchLUTBisectionMethod(Demand, InvLUTPout)

	if SearchResult[1] != 0:
		a = int(SearchResult[0])
		b = int(SearchResult[0] + SearchResult[1])
		#linear interpolation
		m = (InvLUTPin[b] - InvLUTPin[a]) / ( InvLUTPout[b] - InvLUTPout[a]) # slope
		powerin = InvLUTPin[a] + (Demand - InvLUTPout[a]) * m
		#print("a: ",a," b: ",b)
	else:
		powerin = InvLUTPin[int(SearchResult[0])]

	return powerin

#@numba.jit#(nopython = True)
def InverseInverter(PSupplied):
	SearchResult = SearchLUTBisectionMethod(PSupplied, InvLUTPin)

	if SearchResult[1] != 0:
		a = int(SearchResult[0])
		b = int(SearchResult[0] + SearchResult[1])
		#linear interpolation
		m = (InvLUTPout[b] - InvLUTPout[a]) / ( InvLUTPin[b] - InvLUTPin[a]) # slope
		powerout = InvLUTPout[a] + (PSupplied - InvLUTPin[a]) * m
		#print("a: ",a," b: ",b)
	else:
		powerout = InvLUTPout[int(SearchResult[0])]

	return powerout


''' # assuming uniform interval for the x-axis. There's also a bug in the inverse inverter that goes into an infinite loop 
InvLUT = InverterEff.LUT
InvMinPower = InverterEff.MinPower
InvRatedPower = InverterEff.RatedPower 
InvLUTStep = InverterEff.PowerOutStep 
InvTotalSteps = 1 + (InvRatedPower - InvMinPower)/InvLUTStep
import InverterEff

def Inverter0(Demand): # assuming uniform intervals
	indexdummy = (InvTotalSteps -  1) * ((Demand - InvMinPower) / (InvRatedPower - InvMinPower))
	#print('indexdummy: ', indexdummy)
	indexlow = math.floor(indexdummy)
	indexhigh = math.ceil(indexdummy)
	if indexlow == indexhigh:
		powerin = InvLUT[int(indexdummy)]
	else: #linear interpolation
		powerin = InvLUT[indexlow] + (indexdummy - indexlow) * (InvLUT[indexhigh] - InvLUT[indexlow])

	return powerin

def InverseInverter0(PSupplied): # assuming uniform intervals
	MaxDeltaSteps = 13		# max delta PowerIn relative to the Steps/interval in the look up table, use lowest efficiency
	#start with initial index
	indexdummy = int((InvTotalSteps -  1) * ((PSupplied - InvMinPower) / (InvRatedPower - InvMinPower)))
	
	Loop = 1
	while Loop == 1:
		if math.fabs(( (InvLUT[int(indexdummy)] - PSupplied) / InvLUTStep )) < 2: #check LUT. there is a max delta PowerIn
			for i in range (2 * MaxDeltaSteps + 1):

				initiallow = indexdummy - MaxDeltaSteps + i
				#print('dummy index min: ', indexdummy - MaxDeltaSteps + i)
				#print('PSupplied', PSupplied)
				if (initiallow >= 0) & (initiallow < len(InvLUT) - 2): 				
					low = initiallow
					high = low + 1

					print(' low - high', low, '  ', high)

					if (InvLUT[int(low)] <= PSupplied) & (InvLUT[int(high)] >= PSupplied):
						indexlow = int(low)
						indexhigh = indexlow + 1
						print('index found - ')
						Loop = 0
						break
		else:
			indexdummy -= int((InvLUT[int(indexdummy)] - PSupplied) / InvLUTStep) # adjust indexdummy based on how far the PSupplied is from the LUT result
	#print(' end while loop \n')
	#print('indexdummy:',indexdummy,' low:',indexlow,' high',indexhigh)
	Powerindexlow = indexlow * InvLUTStep
	Powerindexhigh = indexhigh * InvLUTStep
	powerout = Powerindexlow + ((Powerindexhigh - Powerindexlow)/(InvLUT[indexhigh] - InvLUT[indexlow])) * (PSupplied - InvLUT[indexlow])

	return powerout
'''

#** RainFlow Method specific for battery cycle computations

def RainFlowMethod(SOC, Temperature):

	PeakValleyIndex =[]
	RainFlowBuffer = deque()
	RainFlowHalfCycle = []
	RainFlowFullCycle = []
	Cycles = []
	PkVyLength = 0

	if len(SOC) >= 2:
		PrevPair = SOC[1] - SOC[0]
		PeakValleyIndex.append(0)

		lastSOC = len(SOC) -1
		# get reversals
		for i in range (len(SOC)):
			if i >= 2:
					CheckPair = SOC[i] - SOC[i-1]
					if PrevPair * CheckPair < 0:
						PeakValleyIndex.append(i-1)
						PrevPair = CheckPair
						ReversalsFound = 1
					elif CheckPair != 0:
						PrevPair = CheckPair

		# rainflow method
		
		# update PeakValleyIndex depending on the latest SOC data
		if len(PeakValleyIndex) >= 3:
			bufferindex = PeakValleyIndex[-1]
			if (SOC[PeakValleyIndex[-1]] - SOC[PeakValleyIndex[-2]])*(SOC[lastSOC] - SOC[PeakValleyIndex[-1]]) < 0:
				PeakValleyIndex.append(lastSOC)
			else:
				PeakValleyIndex.pop()
				PeakValleyIndex.append(lastSOC)
			
		PkVyLength = len(PeakValleyIndex)

	#print('\nPKvyindex = ',PeakValleyIndex)

	if PkVyLength >= 3:
		# start counting cycles given a set of PeakValley points	
		for t in range (PkVyLength):
			RainFlowBuffer.append(PeakValleyIndex[t])
			#print('\n t = ',t)
			while len(RainFlowBuffer) >= 3:
				R1 = math.fabs(SOC[RainFlowBuffer[-2]] - SOC[RainFlowBuffer[-3]])
				R2 = math.fabs(SOC[RainFlowBuffer[-1]] - SOC[RainFlowBuffer[-2]])
				#print('\nR1 = ',R1)
				#print('\nR2 = ',R2)
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
					break # !! this might not be needed or will result to wrong cycles...

		if len(RainFlowBuffer) >= 2:
			for n in range (1,len(RainFlowBuffer)):
				tstartend.append(RainFlowBuffer[n-1]) 	# start of the cycle, referred by the time index
				tstartend.append(RainFlowBuffer[n]) 	# peak or valley of the cycle, referred by the time index
				tstartend.append(RainFlowBuffer[n])		# end of the cycle, referred by the time index
				RainFlowHalfCycle.append(tstartend)
				tstartend = []

		#print('\nRFB: \n',RainFlowBuffer)
		#print('\nFull cycles: \n',RainFlowFullCycle)
		#print('\nHalf cycles: \n',RainFlowHalfCycle)

		for i in range (len(RainFlowFullCycle)):
			DoD = math.fabs(SOC[RainFlowFullCycle[i][0]] - SOC[RainFlowFullCycle[i][1]]) 
			SoC = (SOC[RainFlowFullCycle[i][0]] + SOC[RainFlowFullCycle[i][1]]) / 2
			Temp = (Temperature[RainFlowFullCycle[i][0]] + Temperature[RainFlowFullCycle[i][2]]) / 2
			n = 1
			Crate = DoD * 2 * n  / (RainFlowFullCycle[i][2] - RainFlowFullCycle[i][0]) # !! Assuming Time index is per hour

			cyclelist = []
			cyclelist.append(DoD)
			cyclelist.append(SoC)
			cyclelist.append(Crate)
			cyclelist.append(Temp)
			cyclelist.append(n)
			Cycles.append(cyclelist)

		for i in range (len(RainFlowHalfCycle)):
			DoD = math.fabs(SOC[RainFlowHalfCycle[i][0]] - SOC[RainFlowHalfCycle[i][1]]) 
			SoC = (SOC[RainFlowHalfCycle[i][0]] + SOC[RainFlowHalfCycle[i][1]]) / 2
			Temp = (Temperature[RainFlowHalfCycle[i][0]] + Temperature[RainFlowHalfCycle[i][2]]) / 2
			n = 0.5
			Crate = DoD * 2 * n  / (RainFlowHalfCycle[i][2] - RainFlowHalfCycle[i][0]) # !! Assuming Time index is per hour

			cyclelist = []
			cyclelist.append(DoD)
			cyclelist.append(SoC)
			cyclelist.append(Crate)
			cyclelist.append(Temp)
			cyclelist.append(n)
			Cycles.append(cyclelist)

	else:
		cyclelist = []
		cyclelist.append(1)
		cyclelist.append(1)
		cyclelist.append(1)
		cyclelist.append(1)
		cyclelist.append(0)
		Cycles.append(cyclelist)


	'''			
	# Remove last SOC data from the PeakValleyIndex if necessary
	if (PeakValleyIndex[PkVyLength-1] - PeakValleyIndex[PkVyLength-2])*(SOC[lastSOC] - PeakValleyIndex[PkVyLength-1]) < 0:
		PeakValleyIndex.pop()
	else:
		PeakValleyIndex.pop()
		PeakValleyIndex.append(bufferindex)
	'''


	return Cycles

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

#@numba.jit#(nopython = True)
def BatterySOHDegCalAging(BatSOCAve, Temp4BatAve, BatTime):
	#degradation due to calendar aging
	
	fT = (math.e)**( kTemp * (Temp4BatAve - TempRef) * (TempRef / Temp4BatAve))
	fSOC = (math.e) ** ( -1 * (SOCRef / BatSOCAve) * (((BatSOCAve - SOCRef)/kSOC)**2) )  
	dcal = (BatTime * 3600) * ktimestress * fSOC * fT	
	#print(fT , ' ', fSOC, ' ', dcal)
	#print(BatSOCAve)

	return dcal


#@numba.jit#(nopython = True)
def BatteryDegCycleCalc(Cycle,n): # n = 1 or 0.5 if full or half cycle

	dcyc = 0
	#print(Cycle)
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

#outfile = open('testnewRF.csv','w') # code for debugging only

#@numba.jit#(nopython = True)
def RainFlowCount(RainFlowBuffer):

	CountedHalfFull = 0 # degradation
	RainFlowHalfCycle = []
	RainFlowFullCycle = []

	'''
	h1 = 0
	h2 = 0
	f = 0
	'''

	while len(RainFlowBuffer) >= 3:
		R1 = math.fabs(RainFlowBuffer[-2][1] - RainFlowBuffer[-3][1])
		R2 = math.fabs(RainFlowBuffer[-1][1] - RainFlowBuffer[-2][1])
		#print('\nR1 = ',R1)
		#print('\nR2 = ',R2)
		tstartend = []
		if (R1 < R2) & ( len(RainFlowBuffer) == 3): 
			#print('RFB0',RainFlowBuffer[0])
			#print('RFB1',RainFlowBuffer[1])
			#print('RFB2', RainFlowBuffer[2])
			
			tstartend.append(RainFlowBuffer[0]) # starting of cycle, referred by the time index
			tstartend.append(RainFlowBuffer[1]) # peak/valley of thed cycle, referred by the time index
			tstartend.append(RainFlowBuffer[1]) # ending of cycle, referred by the time index
			RainFlowHalfCycle.append(tstartend)
			tstartend = []
			RainFlowBuffer.popleft()

			#h1 += 1 # code for debugging only

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

			#f += 1 # code for debugging only

		else:
			break 
	if RainFlowHalfCycle != []:
		CountedHalfFull = BatteryDegCycleCalc(RainFlowHalfCycle, 0.5) 
	if RainFlowFullCycle != []:
		CountedHalfFull += BatteryDegCycleCalc(RainFlowFullCycle, 1)

	# code for debugging purspose only
	'''
	row = ''
	row += str(h1) + ','
	row += str(f) + '\n'
	outfile.write(row)
	'''

	return CountedHalfFull # Y

#@numba.jit#(nopython = True)
def RFB2HalfCycles(RainFlowBuffer):

	CountedHalf = 0 # degradation
	RainFlowHalfCycle = []

	#h2 = 0 #code for debugging purpose only

	if len(RainFlowBuffer) >= 2:
		for n in range (1,len(RainFlowBuffer)):
			tstartend = []
			tstartend.append(RainFlowBuffer[n-1]) 	# start of the cycle, referred by the time index
			tstartend.append(RainFlowBuffer[n]) 	# peak or valley of the cycle, referred by the time index
			tstartend.append(RainFlowBuffer[n])		# end of the cycle, referred by the time index
			RainFlowHalfCycle.append(tstartend)

			#h2 += 1

		CountedHalf = BatteryDegCycleCalc(RainFlowHalfCycle,0.5)

	#row = str(h2) + '\n'
	#outfile.write(row)

	return CountedHalf
#@numba.jit#(nopython = True)
def BatterySOHUpdate(d):

	SOH = (1 - pSEI) * ((math.e)**(-1*d)) + pSEI * ((math.e)**(-1*d*rSEI))

	return SOH

