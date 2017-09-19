__author__ = 'Rey Guerrero'

#** 

import csv

# File with header. Exclude header in data (duh)
def ReadListCSVFile(InputFileName, lista):
    #read input csv file
	csv_file = open(InputFileName,"r")
	file_cont = csv.reader(csv_file)

	i = 0

	for line in file_cont:
		if i == 1: # disregard header
			for col in line:
				lista.append(float(col))
		i = 1

	csv_file.close() # close file

def WriteListCSVFile(OutputFileName, lista):
	outfile = open(OutputFileName, 'w')

	for line in lista:
		row = ''
		for col in line:
			row += str(col)
			row += ','
		row += '\n'
		outfile.write(row)

	outfile.close()
