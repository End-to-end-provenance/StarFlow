#!/usr/bin/env python

""" inserts an empty dictionary into the global registry file
required to avoid pickling a non-UTF-8 file and/or a file pickled by Python2
Change the path to the path to the global registry path """

import pickle

d = {}

#Change this path to the path to the global registry file, found in the .starflowcfg dir
with open('/Users/jen/.starflowcfg/.registry', 'wb') as fout:
    pickle.dump(d, fout)
