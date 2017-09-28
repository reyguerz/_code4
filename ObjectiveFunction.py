__author__ = 'Rey Guerrero'

import MonteCarlo
import VarList

def Eval(Scenarios, Sizes, PDFResults):

	Metric2Min = 0													# initialize to zero
	PDFResultFixedSize = []											# initialize to empty list
	PDFResultFixedSize = MonteCarlo.SimScenarios(Scenarios, Sizes)	# Monte Carlo Simulation: different Scenarios, one set of Sizes

	PDFCriteria = VarList.PDFCriteria								# mean, P90, P10, or standard deviation, etc
	ObjectiveMetric = VarList.ObjectiveMetric 						# which column/ metric to optimize

	# compute metric to be minimized
	if (PDFCriteria == 'mean'):										# see VarList for different options
		sum = 0
		for i in range(len(PDFResultFixedSize)):
			sum += PDFResultFixedSize[i][ObjectiveMetric]
		Metric2Min = sum / len(PDFResultFixedSize)
		
	else:															# Add more metric computation as needed
		print('ERROR: PDFCriteria not properly defined. See VarList')
	

	PDFResults += PDFResultFixedSize

	return Metric2Min

# *** test code only
'''
Sizes = [550,540,840]
ECOE = Eval(Sizes)
print ('ECOE Result for Size: ', Sizes, 'is ', ECOE)
'''