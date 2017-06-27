""" basic analysis to demonstrate
writing a python script with annotations
using StarFlow.make_json_prov.StarFlowLL_to_DDG

the final step is to open the output_json_file using DDGExplorer """

import csv, os, numpy as np
import time, datetime
import pickle
import starflow.make_json_prov as JP

input_file = "./data/test1data.csv"
output_file = "./results/test1output.csv"

def manipulate_csv(depends_on=input_file, creates=output_file):
    """ reads csv, adds 5 to each value, and writes csv """
    with open(input_file) as f:
        reader = csv.reader(f)

        reader_list = list(reader)
        entry_length = len(reader_list[0])

        data = np.zeros((len(reader_list), entry_length), dtype = int)

        for i in range (1, len(reader_list)):
            data[i][0] = int(reader_list[i][0])

        for i in range (1, len(data)):
            data[i][0]+=5

        csv_file = open(output_file, 'w')
        for row in data:
            csv_file.write(str(row) + "\n")
        csv_file.close()

        return output_file

def main():
    """ for each function in the workflow, adds an entry to a dictionary with time executed
    makes a LL using StarFlow
    converts this LL to a Prov-JSON file
    the last step is to open output_json_file using DDGExplorer"""

    times_dict = {} # makes a dictionary for the time each function was called

    # arrray of the functions in the order called
    functions = [manipulate_csv]

    for f in functions:
        f # perform the function

        # store the time in the dictionary
        # times_dict[f.__name__] = time.time() # not precise enough?
        current = datetime.datetime.now()
        times_dict[f.__name__] = current.microsecond
        # precision ok for now, make it dynamic/scalable to minutes?

    # pickle dictionary
    times_pickle = open("./results/test1.pickle", 'wb')
    pickle.dump(times_dict, times_pickle)

    times_pickle.close()

    FileList = ['./scripts/test1.py']
    pickle_location = "./results/test1.pickle"
    output_json_file = "./results/test1.json"

    JP.StarFlowLL_to_DDG(FileList, output_json_file, pickle_location)

if __name__ == "__main__":
    main()
