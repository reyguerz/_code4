__author__ = 'Rey Guerrero'

# generated scenarios are stored in a Python data structure
# either generates scenarios of the stochastic variables are computed here or simply read from a file

import AdminFunctions

def Generate(Scenarios):

	# !!! this needs to be consistent with the data structure in Microgrid model.

	Irradiance = []
	WindSpeed = []
	Temp = []
	Demand = []
	OneScenario = []

	'''
	# code for version 1 to 3.
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
	# Kelvin, has one more data point at the start to indicate time = 0 temperature. this is to be used in the battery degradation comp

		
	Dummy = []
	AdminFunctions.ReadListCSVFile('inLoad.csv', Dummy)
	for i in range(20):
		Demand += Dummy

	OneScenario.append(Irradiance)
	OneScenario.append(WindSpeed)
	OneScenario.append(Temp)
	OneScenario.append(Demand)
	Scenarios.append(OneScenario)
	Scenarios.append(OneScenario)

	'''

	# code used for (or starting at) September 2017.

	SolarScenario = 10
	WindScenario = 10
	TempScenario = 1
	DemandScenario = 10
	TotalScenarios = 10 # important. this must be more than one if multiprocessing is implemented.
	fileoffset = 0

	for i in range(SolarScenario):
		infilename = 'input1\PVScenario' + str(i+fileoffset) + '.csv'
		Dummy = []
		AdminFunctions.ReadListCSVFile(infilename,Dummy) # must contain a head (which will be disregarded by the Python code. one column only)
		Irradiance.append(Dummy)

	for i in range(WindScenario):	
		infilename = 'input1\WindScenario' + str(i+fileoffset) + '.csv'
		Dummy = []
		AdminFunctions.ReadListCSVFile(infilename,Dummy)
		WindSpeed.append(Dummy)

	for i in range(DemandScenario):
		infilename = 'input1\LoadScenario20per' + str(i+fileoffset) + '.csv'
		Dummy = []
		AdminFunctions.ReadListCSVFile(infilename,Dummy)
		Demand.append(Dummy)

	infilename = 'input1\TempDataXYears.csv' # already for 20 years with an initial temperature for Battery degradation computation
	AdminFunctions.ReadListCSVFile(infilename,Temp)
	
	
	for i in range(TotalScenarios):
		# !!! this needs to be consistent with the data structure in Microgrid model
		OneScenario = []
		OneScenario.append(Irradiance[i])
		OneScenario.append(WindSpeed[i])
		OneScenario.append(Temp)
		OneScenario.append(Demand[i])
		Scenarios.append(OneScenario)
	'''
	if TotalScenarios > 1:
		for i in range(TotalScenarios):
			# !!! this needs to be consistent with the data structure in Microgrid model
			OneScenario = []
			OneScenario.append(Irradiance[i])
			OneScenario.append(WindSpeed[i])
			OneScenario.append(Temp)
			OneScenario.append(Demand[i])
			Scenarios.append(OneScenario)
	else:
		OneScenario = []
		OneScenario.append(Irradiance[0])
		OneScenario.append(WindSpeed[0])
		OneScenario.append(Temp)
		OneScenario.append(Demand[0])
		Scenarios.append(OneScenario)
	'''
	
	

if __name__ == '__main__':		# this is for testing purposes only
	
	Scenarios = []

	Generate(Scenarios)

	outfilename = 'output\debugpurpose.csv'
	AdminFunctions.WriteListCSVFile(outfilename, Scenarios[0])
	print(len(Scenarios[0]))
	print(len(Scenarios[0][2]))