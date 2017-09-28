__author__ = 'Rey Guerrero'

#** version: 22 September 2017 

import csv

# File with header. Exclude header in data (duh). Multiple columns
def ReadMultiListCSVFile(InputFileName):


    #read input csv file
	csv_file = open(InputFileName,"r")
	file_cont = csv.reader(csv_file)

	# initialize variables
	MultiList = []
	i = 0

	for line in file_cont:
		if i == 1: # disregard header
			lista = []
			for col in line:
				lista.append(float(col))
			MultiList.append(lista)
		i = 1

	csv_file.close() # close file

	return MultiList


# File with header. Exclude header in data (duh). One column only...
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

def WriteListCSVFile(OutputFileName, lista): # multiple columns
	outfile = open(OutputFileName, 'w')

	for line in lista:
		row = ''
		for col in line:
			row += str(col)
			row += ','
		row += '\n'
		outfile.write(row)

	outfile.close()

# one column only
def WriteOneListCSVFile(OutputFileName, lista):
	outfile = open(OutputFileName, 'w')

	for item in lista:
		row = ''
		row += str(item)
		row += '\n'
		outfile.write(row)

	outfile.close()