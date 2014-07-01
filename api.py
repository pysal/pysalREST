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


def checktypes(call, *args, **kwargs):
    docs = inspect.getdoc(call)
    for d in docs.split('\n'):
        print d

def extractmethods(package, funcs):
    """
    Naively iterate through a package, access all the modules, and get all the function
    and class names.

    Returns a dict of dicts where the top level is the module name.  The value of
    each module name is another dict containing the available funcs and classes.
    """
    #Two pass algorithm - this only happens on launch or refresh.
    for mn, m in inspect.getmembers(package):
        mn = mn.lower()
        #Parse at the module level first
        if isinstance(m, types.ModuleType):
            funcs[mn] = m

    for k, module in funcs.iteritems():
        k = k.lower()
        funcs[k] = {}
        for mn, m in inspect.getmembers(module):
            mn = mn.lower()
            if m == '__builtins__':
                continue
            if isinstance(m, types.FunctionType) or isinstance(m, types.ClassType):
                funcs[k][mn] = m

            #ESDA has this strange nesting in the module structure.
            # This is a hacky solution that should be recursive...
            elif isinstance(m, types.ModuleType):
                for nestedmn, nestedm in inspect.getmembers(m):
                    nestedmn = nestedmn.lower()
                    if isinstance(nestedm, types.FunctionType) or isinstance(nestedm, types.ClassType):
                        funcs[k][nestedmn] = nestedm
    return funcs

def getwrapper(func, *args, **kwargs):
    """
    Generic function wrapper for GET requests.
    """
    return func(args, kwargs)


def postwrapper(func, args, kwargs):
    """
    Generic function wrapper for POST requests.
    """
    return func(args, kwargs)


def get(module, method=None, **kwargs):
    """
    Handles HTTP GET requests.

    module: PySAL module level, e.g. weights or spreg
    method: PySAL sub module level, eg. weights.queen_from_shapefile
    """
    module = module.lower()
    method = method.lower()
    try:
        method = funcs[module][method]
    except:
        available_funcs = [k for k in funcs[module].iterkeys()]
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
    if method is None:
        return pr.OkResponse('Need to supply a method call.')
    #Send the args, kwargs to the wrapper to unpack and call PySAL
    print func(np.ndarray(args[0]), args[1])
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
    print kwargs, len(kwargs.keys())
    if len(kwargs.keys()) == 0:
        return pr.MalformedResponse('Need to supply some arguments')
    else:
        module, func = kwargs['func'].split('/')
        method = funcs[module.lower()][func.lower()]

        args = ast.literal_eval(kwargs['args'])
        #Hack to get FJ working - it expects an array
        newargs = []
        for i, a in enumerate(args):
            if isinstance(a, list):
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


funcs = {}
package = ps
funcs = extractmethods(package, funcs)

