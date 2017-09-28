__author__ = 'Rey Guerrero'

# main program

import sys
import os

# Initialization. Import functions and modules
import ScenarioGen
import SimulatedAnnealing
import AdminFunctions

def main():

	# define variables
	Scenarios = []				# input stochastic variable during simulations
	PDFResults = []				# simulation intermediary and results
	DesignResult = []			# metric that is minimized by the optimization algorithm



	# for runtime computation
	from datetime import datetime
	starttime = datetime.now()


	# Scenario Gen: generates scenarios of meteorological and load data
	print('Generating Scenarios...')
	ScenarioGen.Generate(Scenarios)

	# Optimization Algorithm that calls MCS which in turn calls the MicrogridModel Simulation
	#SimulatedAnnealing.SAOptimize(Scenarios, PDFResults, DesignResult)
	SimulatedAnnealing.SAPassThru(Scenarios, PDFResults, DesignResult) # for test purpose only


	# Output Results
	#print('Design Result: [Size],Scenario Index, ECOE:')
	#print(PDFResults)

	Header = ['PVSize', 'WTSize', 'BatSize', 'ScenarioID','ECOE','TotalCost','TotalDemandServed']	
	PDFResults.insert(0, Header)
	outfilename = 'output\SimulationResults.csv'
	AdminFunctions.WriteListCSVFile(outfilename, PDFResults)

	# run time computation and end of program
	stoptime = datetime.now()

	print ('runtime: ',stoptime - starttime)
	print('\nDone! Good luck! \nPress Enter to Exit Program')
	ExitEnter = input()


if __name__ == '__main__':		# this is needed for Python multiprocessing to work in Windows 
	main()