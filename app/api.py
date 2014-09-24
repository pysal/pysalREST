import sys
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

def extractmethods(package, funcs):
    """
    Naively iterate through a package, access all the modules, and get all the function
    and class names.

    Returns a dict of dicts where the top level is the module name.  The value of
    each module name is another dict containing the available funcs and classes.
    """
    #Two pass algorithm - this only happens on launch or refresh.

    for mn, m in inspect.getmembers(ps):
        if inspect.ismodule(m):
            funcs[mn] = m

    for k, module in funcs.iteritems():
        funcs[k] = {}
        for mn, m in inspect.getmembers(module):
            if mn[:2] == '__':
                continue
            elif inspect.isclass(m):
                funcs[k][mn] = m
            elif inspect.isfunction(m):
                funcs[k][mn] = m
                #print "FUNC: ", k, mn, m
            elif inspect.ismodule(m):
                funcs[k][mn] = {}
                for nestedobjname, nestedobj in inspect.getmembers(m):
                    if nestedobjname[:2] == '__':
                        continue
                    elif inspect.isclass(nestedobj):
                        funcs[k][mn][nestedobjname] = nestedobj
                        #print "CL: ", k,nestedmodulename, nestedmodule
                    elif inspect.isfunction(nestedobj):
                        funcs[k][mn][nestedobjname] = nestedobj
                        #print "FUNC: ", k, nestedmodulename, nestedmodule

            '''
            #ESDA has this strange nesting in the module structure.
            # This is a hacky solution that should be recursive...
            elif isinstance(m, types.ModuleType):
                for nestedmn, nestedm in inspect.getmembers(m):
                    if nestedm == '__builtins__':
                        continue
                    if isinstance(nestedm, types.FunctionType) or isinstance(nestedm, types.ClassType):
                        funcs[k][nestedmn] = nestedm
                        print k, nestedmn, nestedm
            '''
    return funcs

def extractmethods_init(package, funcs):
    userexposedmodules = inspect.getsource(package)
    gotversion = False
    for l in userexposedmodules.rsplit('\n'):
        if 'pysal.version' in l:
            gotversion = True
        if gotversion is False:
            continue

        #Insane source code parsing to get the user exposed classes dynamically
        if len(l) > 0:
            if l[0] == '#':
                continue
            if l.startswith('import'):
                break
            else:
                line = l.split()
                if line[0] == 'from':
                    keys = line[1]
                    modules =  keys.split('.')[1:]
                    if line[-1] == '\\':
                        line.remove('\\')
                    currentdict = funcs
                    for i in modules:
                        if i not in currentdict.keys():
                            funcs[i] = {}
                            currentdict = funcs[i]
                    for i in line[3:]:
                        currentdict[i] = None
                else:
                    line = l.split()





funcs = {}
package = ps
funcs = extractmethods(package, funcs)
