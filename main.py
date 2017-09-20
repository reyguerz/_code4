__author__ = 'Rey Guerrero'

# main program

import sys
import os

# Initialization. Import functions and modules
import ScenarioGen
import SimulatedAnnealing

# define variables
Scenarios = []				# input stochastic variable during simulations
PDFResults = []				# simulation intermediary and results
DesignResult = []			# metric that is minimized by the optimization algorithm



# for runtime computation
from datetime import datetime
starttime = datetime.now()


# Scenario Gen: generates scenarios of meteorological and load data
ScenarioGen.Generate(Scenarios)

# Optimization Algorithm that calls MCS which in turn calls the MicrogridModel Simulation
SimulatedAnnealing.SAOptimize(Scenarios, PDFResults, DesignResult)

# Output Results
print('Design Result: [Size],ECOE:',DesignResult)



# run time computation and end of program
stoptime = datetime.now()

print ('runtime: ',stoptime - starttime)
print('\nDone! Good luck! \nPress Enter to Exit Program')
ExitEnter = input()
