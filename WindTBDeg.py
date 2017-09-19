__author__ = 'Rey Guerrero'

# Python Code for Wind TB Degradation Look Up Table
TimeStep = 1 # 1 day, assume equal interval of one day
TotalSteps = 7300 #total number of days, 20 years * 365 days
AnnualDeg = -0.016 # yearly degradation

LUT = []

for i in range(TotalSteps):
	eff = 1 + AnnualDeg*((i+1)/365)
	LUT.append(eff)
