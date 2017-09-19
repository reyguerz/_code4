__author__ = 'Rey Guerrero'

'''
InitialTemperature = 50 # Katsigiannis 

Define ObjectiveFunction # for ECOE, the lower the better

InitialSolution
	random x and y
	Compute ObjectiveFunction

Perturb
	randomly choose parameter to change
	change the chosen parameter
		parameters are within acceptable / feasible range
		check if the new config was already computed before
	Compute ObjectiveFunction
		check for reliability

	Metropolis Algorithm
		Generate random v between 0 and 1
		delta = difference in ObjectiveFunction
		if delta < 0, choose as new parameter # new solution is better than old solution
		elif e^ ( - (delta) / Temp ) < v
	
	Repeat until 30x

Change Temp. Repeat Perturb. Until Temp = Min Temp. # Min Temp is the "resolution"	
'''

# initialization
import math
import csv
import ObjectiveFunction
import MicrogridModel
import random
import AdminFunctions

from datetime import datetime
starttime = datetime.now()


TabuList = []
TabuListandResults = []


#****** FUNCTION DEFINITIONS

def SolFinder(Sizes): 
		# Checks if Sizes or Solution were already solved before and are in the Tabu List 
		# Checks if Sizes are also within Constraints of the Microgrid Reliability / Design
		# 
	SolFound = 0
	Metric1 = 0

	if (Sizes in TabuList) == 0: # Sizes is unique and not yet computed
		TabuList.append(Sizes)
		Metric1 = ObjectiveFunction.Eval(Sizes)
		SizeandResult = []
		SizeandResult.append(Sizes[0])
		SizeandResult.append(Sizes[1])
		SizeandResult.append(Sizes[2])
		SizeandResult.append(Metric1)
		TabuListandResults.append(SizeandResult)
		if Metric1 < MicrogridModel.ECOEPenalty1:
			SolFound = 1
	else:
		SolFound = 0 # need to look for another set of sizes/solution

	Result = []
	Result.append(SolFound)
	Result.append(Metric1)

	return Result

def newTempGeometric(Temp):

	alpha = 0.5

	return alpha*Temp

# ********* END FUNCTION DEFINITIONS




# ***** SIMULATED ANNEALING

#output to CSV
OutFileName = 'SATestOutput.csv'
outfile = open(OutFileName,'w')

# SA initialization
InitialTemp = 10	# initial temperature can be the worst feasible solution
TempMin = 0.001		# TempMin is ideally the resolution / error of the solution or how different the previous solution is with the found optimal solution
Temp = InitialTemp
MarkovChainLength = 30
NumberofInputParameters = 3


# min and max sizes 
#!! Important. Note the unit size step in the MicrogridModel. default is at 1kW or 1kWh for battery
PVSizeMin = 0
PVSizeMax = 1000 	# Aveload * 24 * 24
PVSizeRes = 5		# note the unit size. default is 1kW
WTSizeMin = 0
WTSizeMax = 1000
WTSizeRes = 20
BatSizeMin = 5
BatSizeMax = 1000
BatSizeRes = 5



# initial solution
print('Solving Initial Solution...')
SolFound = 0

while SolFound == 0:

	PVSize = PVSizeRes * random.randint(PVSizeMin/PVSizeRes,PVSizeMax/PVSizeRes)
	WTSize = WTSizeRes * random.randint(WTSizeMin/WTSizeRes, WTSizeMax/WTSizeRes)
	BatSize = BatSizeRes * random.randint(BatSizeMin/BatSizeRes, BatSizeMax/BatSizeRes)
	Sizes1 = []
	Sizes1.append(PVSize)
	Sizes1.append(WTSize)
	Sizes1.append(BatSize)

	Result = SolFinder(Sizes1)

	SolFound = Result[0] 

Sol1 = Result[1]
print('Initial Solution: ',Sol1, Sizes1)

# Annealing
while (Temp > TempMin):
	for i in range(MarkovChainLength):

		row = []
		row = str(Temp) + ',' + str(i) + ',' + str(Sizes1[0]) + ',' + str(Sizes1[1]) + ',' + str(Sizes1[2]) + ',' + str(Sol1) + '\n' 
		outfile.write(row)
		print('Temp:',Temp, 'i:',i,' PV = ',Sizes1[0],' WT = ',Sizes1[1], ' Bat = ',Sizes1[2],' val = ', Sol1)

		# Find neighbor, Perturb
		SolFound = 0
		while SolFound == 0:
			Sizes2 = []
			RandParam = random.randint(0,(NumberofInputParameters-1))
			if RandParam == 0:
				Sizes2.append(PVSizeRes * random.randint(PVSizeMin/PVSizeRes,PVSizeMax/PVSizeRes))
				Sizes2.append(Sizes1[1])
				Sizes2.append(Sizes1[2])
			elif RandParam == 1:
				Sizes2.append(Sizes1[0])
				Sizes2.append(WTSizeRes * random.randint(WTSizeMin/WTSizeRes, WTSizeMax/WTSizeRes))
				Sizes2.append(Sizes1[2])
			elif RandParam == 2:
				Sizes2.append(Sizes1[0])
				Sizes2.append(Sizes1[1])
				Sizes2.append(BatSizeRes * random.randint(BatSizeMin/BatSizeRes, BatSizeMax/BatSizeRes))
			
			Result = SolFinder(Sizes2)

			SolFound = Result[0]


		Sol2 = Result[1]

		delta = Sol2 - Sol1

		if delta < 0:
			Sol1 = Sol2
			Sizes1 = Sizes2
			
		elif math.exp( -1*delta/Temp) > random.random():
			Sol1 = Sol2
			Sizes1 = Sizes2

	Temp = newTempGeometric(Temp)

AdminFunctions.WriteListCSVFile('SATabuList.csv',TabuListandResults)

#******** EXIT

stoptime = datetime.now()

print ('runtime: ',stoptime - starttime)
print('\nDone! Good luck! \nPress Enter to Exit Program')
ExitEnter = input()



