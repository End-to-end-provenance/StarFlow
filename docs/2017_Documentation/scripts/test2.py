#!/usr/bin/env python

""" Script annotations for StarFlow

There are multiple ways to annotate functions; the main components are the keywords
'depends_on' and 'creates'.

The depends_on keyword is used for typical inputs of a function.
These inputs could include filenames from which the data is read,
or objects, pieces of data, functions, or other parameters.

The creates keyword is used for defining the output files to which a function writes its results.

In the 1st example function, parse(), the keywords are included in the function definition.
The filenames are defined at the beginning of the file.

In the 2nd example add(), the depends_on keyword refers to a list,
because the function depends on the infile from which to read the data, and
the input_value that is added to each element in the array.

In the last example function, compare(), the keywords are included in the wrapper function, Compare().
The filenames are defined in the wrapper function definition.
"""

import numpy as np
import time, datetime
import pickle
import starflow.make_json_prov as JP

# from project directory, use ./data/first.csv
# from inside the scripts directory, use ..data/first.csv

infile = "./data/first.csv"
outfile = "./data/second.csv"
input_value = 2
#when using depends_on and creates directly, as in parse(), must define files before function definition
add_file = "./data/added.csv"

def parse(depends_on = infile, creates = outfile):
    csv = np.genfromtxt(infile, delimiter = ",", dtype = int)
    pivoted_csv = csv.transpose()
    np.savetxt(outfile, pivoted_csv, fmt= '%u', delimiter = ',')

def add(depends_on = (outfile, input_value), creates = (add_file)):
    csv = np.genfromtxt(outfile, delimiter = ",", dtype = int)
    added_csv = csv + input_value
    np.savetxt(add_file, added_csv, fmt= '%u', delimiter = ',')

def times_two(depends_on = outfile, creates = "./data/mult.csv"):
    csv = np.genfromtxt(outfile, delimiter = ",", dtype = int)
    mult_csv = csv*2
    np.savetxt(creates, mult_csv, fmt= '%u', delimiter = ',')

def Compare(depends_on = ('./data/added.csv', './data/mult.csv'), creates = './results/diff.csv'):
    #when using wrapper function, define files here
    compare(depends_on[0], depends_on[1], creates)

def compare(added_file, mult_file, outfile):
    added_csv = np.genfromtxt(added_file, delimiter = ",", dtype = int)
    mult_csv = np.genfromtxt(mult_file, delimiter = ",", dtype = int)
    diff = mult_csv - added_csv
    np.savetxt(outfile, diff, fmt= '%u', delimiter = ',')

def main():
    """ for each function called, adds an entry to a dictionary with time executed
    calls StarFlowLL_to_DDG to create a Prov-JSON file that can be read using DDGExplorer"""

    times_dict = {} # makes a dictionary for the time each function was called

    # arrray of the functions in the order called
    functions = [parse, add, times_two, Compare]

    for f in functions:
        f # perform the function

        # store the time in the dictionary
        # times_dict[f.__name__] = time.time() # not precise enough?
        current = datetime.datetime.now()
        times_dict[f.__name__] = current.microsecond
        # precision ok for now, make it dynamic/scalable to minutes?

    # pickle dictionary for later use
    times_pickle = open("./results/test2.pickle", 'wb')
    pickle.dump(times_dict, times_pickle)

    times_pickle.close()

    FileList = ['./scripts/test2.py']
    pickle_location = "./results/test2.pickle"
    output_json_file = "./results/test2.json"

    JP.StarFlowLL_to_DDG(FileList, output_json_file, pickle_location)

    # open the output_json_file using DDGExplorer

if __name__ == "__main__":
    main()
