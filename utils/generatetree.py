from collections import Mapping
import copy
import os
import json
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))
from extractapi import recursive_extract
import config


"""
The idea here is that library functions could be swapped
to be a JSON file or the underlying logic can change.

The only requirement is that this is a dictionary with
a most nested level of 'function_name':func_object pairs.
"""

def walk_dict(d):
    for k,v in d.items():
        if isinstance(v, dict):
            walk_dict(v)
        else:
            d[k] = True

def generate_map(outfile):
    visited = set([])
    libraryfunctions = {}
    
    library = __import__(config.library)
    recursive_extract(library, libraryfunctions, library.__name__, visited)

    #Recursive function extraction
    librarydocs = copy.deepcopy(libraryfunctions)

    mapping = copy.deepcopy(libraryfunctions)
    walk_dict(mapping)
    with open(outfile, 'w') as mapfile:
        mapfile.write(json.dumps(mapping, indent=2))

def usage():
    print "Please supply an output file name for the library mapping, e.g. mylibrary.json"

if __name__ == '__main__':
    if len(sys.argv) <= 1:
	usage()
	sys.exit()
    generate_map(sys.argv[1])
