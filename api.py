import pysalrest as pr
import pysal as ps
import inspect
import ast
import types
import json

import numpy as np

"""
URL Format
with kwargs: http://localhost:8080/api/api/queen_from_shapefile?args=['columbus.shp']&kwargs={'idVariable':'field'}
w/o kwargs: http://localhost:8080/api/api/queen_from_shapefile?args=['columbus.shp']
"""


def extractmethods(package, funcs):
    """
    Naively iterate through a package, access all the modules, and get all the function
    and class names.
    """
    for mn, m in inspect.getmembers(package):
        if isinstance(m, types.ModuleType):
            for nested_mn, nested_m in inspect.getmembers(m):
                if nested_mn == '__builtins__':
                    continue
                if isinstance(nested_m, types.FunctionType) or isinstance(nested_m, types.ClassType):
                    funcs[nested_mn] = nested_m
        elif isinstance(m, types.FunctionType):
            funcs[mn] = m
    return funcs

funcs = {}
package = ps
funcs = extractmethods(package, funcs)


class CustomJsonEncoder(json.JSONEncoder):
    """
    Custom JSON Encoder that supports numpy arrays and
    class objects.

    Note: Class objects are returned as dict representations.
    """
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.generic):
            return  obj.item()
        else:
            return obj.__dict__
        return json.JSONEncoder.default(self,obj)


def getwrapper(func, args, **kwargs):
    """
    Generic function wrapper for GET requests.
    """
    return func(args, kwargs)


def postwrapper(func, args, kwargs):
    """
    Generic function wrapper for POST requests.
    """
    return func(args, kwargs)


def get(ref=None, **kwargs):
    """
    Handles HTTP GET requests.
    """

    try:
        method = funcs[ref]
    except:
        available_funcs = [k for k in funcs.iterkeys()]
        return pr.ErrorResponse("Unknown method.  Available methods are: {}".format(available_funcs))

    #Parse the args and kwargs
    try:
        strargs = kwargs['args']
        args = ast.literal_eval(strargs)
    except:
        try:
            reqargs = inspect.getargspec(method)[0]
        except:
            reqargs = inspect.getargspec(method.__init__)[0]
            reqargs.remove('self')
        return pr.ErrorResponse('Missing required argument: {}'.format(reqargs))
    try:
        strkwargs = kwargs['kwargs']
        kwargs = ast.literal_eval(strkwargs)
    except:
        #User has not supplied kwargs
        kwargs = {}

    if ref is None:
        return pr.OkResponse('Need to supply a method call.')

    #Send the args, kwargs to the wrapper to unpack and call PySAL
    result = getwrapper(method, *args, **kwargs)
    try:
        json.dumps(result)
        return pr.OkResponse(result)
    except:
        return pr.OkResponse(json.dumps(result, cls=CustomJsonEncoder))


def post(**kwargs):
    """
    Handles HTTP POST requests
    """

    if len(kwargs.keys()) == 0:
        return pr.MalformedResponse('Need to supply some arguments')
    else:
        method = funcs[kwargs['func']]
        args = ast.literal_eval(kwargs['args'])

        #Hack to get FJ working - it expects an array
        newargs = []
        for i, a in enumerate(args):
            if isinstance(a, list):
                print a
                newargs.append(np.array(a))
            else:
                newargs.append(a)
        args = tuple(newargs)
        #Hack Done

        try:
            kwargs = ast.literal_eval(kwargs['kwargs'])
        except:
            kwargs = {}

        #Call the wrapper to execute the function
        result = postwrapper(method, *args, **kwargs)

        try:
            json.dumps(result)
            return pr.OkResponse(result)
        except:
            return pr.OkResponse(json.dumps(result, cls=CustomJsonEncoder))

