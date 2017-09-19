__author__ = 'Rey Guerrero'

import MicrogridModel

def Eval(Sizes):

	MicrogridModel.PVSize = Sizes[0]	# double check components for unit size
	MicrogridModel.WTSize = Sizes[1]	# double check components and WT LUT code for unit size
	MicrogridModel.BatSize = Sizes[2] 	# double check components and code below for unit size

	ECOE = MicrogridModel.Simulation()

	return ECOE

# *** test code only

Sizes = [550,540,840]
ECOE = Eval(Sizes)
print ('ECOE Result for Size: ', Sizes, 'is ', ECOE)
