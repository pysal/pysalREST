import pysalrest as pr
import pysal as ps
import inspect
import ast
import types

"""
URL Format
with kwargs: http://localhost:8080/api/api/queen_from_shapefile?args=['columbus.shp']&kwargs={'idVariable':'field'}
w/o kwargs: http://localhost:8080/api/api/queen_from_shapefile?args=['columbus.shp']
"""

funcs = {}
package = ps

for mn, m in inspect.getmembers(package):
    if isinstance(m, types.ModuleType):
        for nested_mn, nested_m in inspect.getmembers(m):
            if nested_mn == '__builtins__':
                continue
            if isinstance(nested_m, types.FunctionType) or isinstance(nested_m, types.ClassType):
                funcs[nested_mn] = nested_m
    elif isinstance(m, types.FunctionType):
        funcs[mn] = m

def wrapper(func, args, **kwargs):
    return func(args, kwargs)

def get(ref=None, **kwargs):

    try:
        method = funcs[ref]
    except:
        available_funcs = [k for k in funcs.iterkeys()]
        return pr.ErrorResponse("Unknown method.  Available methods are: {}".format(available_funcs))

    #Parse the args and kwargs
    strargs = kwargs['args']
    args = ast.literal_eval(strargs)
    try:
        strkwargs = kwargs['kwargs']
        kwargs = ast.literal_eval(strkwargs)
    except:
        #User has not supplied kwargs
        kwargs = {}

    if ref is None:
        return pr.OkResponse('Need to supply a method call.')

    #Send the args, kwargs to the wrapper to unpack and call PySAL
    result = wrapper(method, *args, **kwargs)
    try:
        json.dumps(result)
        return pr.OkResponse(result)
    except:
        return pr.OkResponse(result.neighbors)

def test(args, IdVariable=None):
    print args
    print IdVariable

def post(message=None):
    if message is None:
        return pr.MalformedResponse('Need to supply some arguments')
