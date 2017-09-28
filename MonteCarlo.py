__author__ = 'Rey Guerrero'


import multiprocessing
import functools

import VarList
import MicrogridModel


#*** Monte Carlo Simulation

def MicrogridSim(Scenarios,Sizes,x): 			# function to simulate microgrid
	
	metrics = []
	metrics = MicrogridModel.Simulation(Scenarios[x], Sizes)
	metrics = Sizes + [x] + metrics				# append Sizes and scenario index/identifier
	return metrics

def SimScenarios(Scenarios, Sizes):

	PDFResultFixedSize = []

	
	''' # single process only
	for i in range(len(Scenarios)):
		metrics = []												# initialize/empty metrics data
		metrics = MicrogridModel.Simulation(Scenarios[i], Sizes)	# simulate microgrid for one scenario and sizes. output set of metrics
		metrics = Sizes + [i] + metrics								# append scenario identifier and sizes at the beginning of the list
		PDFResultFixedSize.append(metrics)							# compile results of different scenarios with one size
	
	'''
	
	# multiprocessing
	pool = multiprocessing.Pool(VarList.NumberofParallelProcesses)			# initialize pool with number of process or "workers"
	PartialFunction = functools.partial(MicrogridSim, Scenarios, Sizes)		# partial function to "fix" Scenario and Sizes input when multi processing
	PDFResultFixedSize = pool.map(PartialFunction, range(len(Scenarios)))	# multi processing proper, with third argument of Microgrid Sim increasing from 0 to last index of Scenerios
	pool.close()		# tells that there's no more work to do for the processes
	pool.join()			# ready for other work(?)
	

	return PDFResultFixedSize

