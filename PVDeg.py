__author__ = 'Rey Guerrero'

# Python Code for PV Degradation Look Up Table

import VarList

TimeStep = 1 # 1 day, assume equal interval of one day
TotalSteps = 7300 #total number of days, 20 years * 365 days
PVAnnualDeg = VarList.PVAnnualDeg # yearly degradation, linear degradation

LUT = []

for i in range(TotalSteps):
	eff = 1 + PVAnnualDeg*((i+1)/365) 
	LUT.append(eff)
