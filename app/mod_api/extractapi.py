import collections
import inspect
import json
import types

import w_from_geojson

def extractsubsub(package, d):
    sub_modules = inspect.getmembers(package, inspect.ismodule)
    functions = inspect.getmembers(package, inspect.isfunction)
    classes = inspect.getmembers(package, inspect.isclass)

    for functionname, function in functions:
        d[functionname] = function

    for classname, classobj in classes:
        d[classname] = classobj

    for modulename, module in sub_modules:
        pass
    return d

def extractsub(package, d):
    sub_modules = inspect.getmembers(package, inspect.ismodule)
    functions = inspect.getmembers(package, inspect.isfunction)
    classes = inspect.getmembers(package, inspect.isclass)

    for functionname, function in functions:
        d[functionname] = function

    for classname, classobj in classes:
        d[classname] = classobj

    for modulename, module in sub_modules:
        d[modulename] = {}
        if module.__package__ != None and 'pysal' in module.__package__:
            d[modulename] = extractsubsub(module, d[modulename])

    return d

def extract(package, pysalfunctions):
    sub_modules = inspect.getmembers(package, inspect.ismodule)
    functions = inspect.getmembers(package, inspect.isfunction)
    classes = inspect.getmembers(package, inspect.isclass)

    pysalfunctions['TopLevel'] = {}

    for functionname, function in functions:
        pysalfunctions['TopLevel'] [functionname] = function

    for classname, classobj in classes:
        pysalfunctions['TopLevel'] [classname] = classobj

    for modulename, module in sub_modules:
        pysalfunctions[modulename] = {}
        if module.__package__ != None and 'pysal' in module.__package__:
            pysalfunctions[modulename] = extractsub(module,pysalfunctions[modulename])

    #Add the custom geojson_functions
    pysalfunctions['weights']['queen_from_geojson'] = w_from_geojson.queen_geojson

    return pysalfunctions
