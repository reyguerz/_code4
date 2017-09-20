__author__ = 'Rey Guerrero'


import MicrogridModel

#*** Monte Carlo Simulation

def SimScenarios(Scenarios, Sizes, PDFResultFixedSize):

	for i in range(len(Scenarios)):
		metrics = []												# initialize/empty metrics data
		MicrogridModel.Simulation(Scenarios[i], Sizes, metrics)		# simulate microgrid for one scenario and sizes. output set of metrics
		metrics = Sizes + [i] + metrics								# append scenario identifier and sizes at the beginning of the list
		PDFResultFixedSize.append(metrics)							# compile results of different scenarios with one size
		