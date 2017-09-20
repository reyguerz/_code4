__author__ = 'Rey Guerrero'

# generated scenarios are stored in a Python data structure
# either generates scenarios of the stochastic variables are computed here or simply read from a file

import AdminFunctions

def Generate(Scenarios):
	Irradiance = []
	WindSpeed = []
	Temp = []
	Demand = []
	OneScenario = []

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

	# !!! this needs to be consistent with the data structure in Microgrid model

	OneScenario.append(Irradiance)
	OneScenario.append(WindSpeed)
	OneScenario.append(Temp)
	OneScenario.append(Demand)

	Scenarios.append(OneScenario)
