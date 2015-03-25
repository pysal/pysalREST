import ast
from collections import OrderedDict
import cPickle
import hashlib
import inspect
import re
import time
from urlparse import urlparse

import numpy as np
import pysal as ps
import requests

from flask import g      
from pmd import pmdwrapper
from app import libraryfunctions, librarydocs, db
from config import baseurl, basedataurl


from app.mod_data.models import UserPyObj

def getargorder(call):
    """
    Get the order of required args from a function.
    Does not support *args currently.
    """

    try:
        args = inspect.getargspec(call)
	try:
	    nargs = len(args.args)
	except:
	    nargs = 0 
	try:
	    ndef = len(args.defaults)
	except:
 	    ndef = 0
	nreqargs = nargs - ndef
	argorder = args.args[:nreqargs]	
    except:
        args = inspect.getargspec(call.__init__)
	try:
	    nargs = len(args.args)
	except:
	    nargs = 0
	try:	
	    ndef = len(args.defaults)
	except:
	    ndef = 0
	nreqargs = nargs - ndef
	argorder = args.args[1:nreqargs] #Ignore self
    print argorder
    return argorder

def gettoken(a):
    url = False
    try:
	o = urlparse(a)
	
	if o.scheme in ['http', 'https', 'ftp']:
		url = True
    except:pass
    #If 'a' is a url, get the json data
    if url:
	if 'raw' in o.path.split('/'):
	    r = requests.get(a, verify=False)
            try:
		a = cPickle.loads(r.content)
		return a
	    except:
		print "ERROR: Can not load RAW data as a Python Object"
	else:
            r = requests.get(a, verify=False).json()
	    try:
                a = r['data']
	        return a
	    except: pass
    return False


def post(request, module,method, module2=None):
    """
    To make a POST using CURL:
    Fisher-Jenks using the Hartigan Olympic time example
    curl -i -H "Content-Type: application/json" -X POST -d '{"args":["[12, 10.8, 11, 10.8, 10.8, 10.6, 10.8, 10.3, 10.3,10.3,10.4,10.5,10.2,10.0,9.9]"], "kwargs":{"k":5}}' http://localhost:8080/api/esda/mapclassify/Fisher_Jenks/

    or

    Using the CherryPy server on port 8080
    Queen from shapefile - NOTE: The file must be uploaded already
    curl -i -H "Content-Type: application/json" -X POST -d '{"args":[NAT.shp]}' http://localhost:8080/api/weights/queen_from_shapefile/
    
    or

    curl -i -k -H "Content-Type: application/json" -u jay@jay.com:jay -X POST -d '{"args":{y":[12, 10.8, 11, 10.8, 10.8, 10.6, 10.8, 10.3, 10.3,10.3,10.4,10.5,10.2,10.0,9.9]}, "kwargs":{"k":5}}' https://webpool.csf.asu.edu/pysalrest/api/esda/mapclassify/Fisher_Jenks/
    """
    if not request.json:
        response = {'status':'error','data':{}}
        response['data'] = 'Post datatype was not json'
        return jsonify(response), 400
    else:
        response = {'status':'success','data':{}}
        #Setup the call, the args and the kwargs
       	
	#TODO: This needs to be cleans so that manual 2 module traversal is automated... 
	if module2 == None:
	    argorder = getargorder(libraryfunctions[module][method])
	    call = libraryfunctions[module][method]
            #call = pmdwrapper(libraryfunctions[module][method])
        else:
	    argorder = getargorder(libraryfunctions[module][module2][method])
            call = libraryfunctions[module][module2][method]
	    #call = pmdwrapper(libraryfunctions[module][module2][method])
        #Parse the args
        keys = request.json.keys()
        req = request.json
        #Setup the python arg / kwarg containers
        args = []
        kwargs = {}
        
	if 'arguments' in req.keys():
	    arguments = req['arguments']
	    if 'required_arguments' in arguments.keys():
		for a in argorder:
		    #Check if the arg is a URL or raw data
       		    try:
		        v = arguments['required_arguments'][a]
		    except:
		        a_key = '{}_href'.format(a)
		        v = arguments['required_arguments'][a_key]
			try:
			    v = gettoken(v)  #Grab the data via the token
		 	except:
	    		    return {'status':'failure', 'message':'Unable to get data from url: {}'.format(v)}
			
 		    #Convert to a Python object
		    try:
			pythonarg = ast.literal_eval(v)
		    except:
			pythonarg = v
	
		    if isinstance(pythonarg, list):
			pythonarg = np.array(pythonarg)
		    args.append(pythonarg)

	    if 'optional_arguments' in arguments.keys():
	    	for k, v in arguments['optional_arguments'].iteritems():
		    if '_href' in k:
			try:
			    v = gettoken(v)
			    k = k.split('_')[0]  #clean the _href off
			except:	
	    		    return {'status':'failure', 'message':'Unable to get data from url: {}'.format(v)}
	    	    
		    #Convert to a python object
		    try:
		 	pythonarg = ast.literal_eval(v)
		    except:
			pythonarg = v
		    
		    #Cast to a ndarray
		    if isinstance(v, list):
			v = np.array(v)

		    kwargs[k] = v

	#Explicit duck typing
        #Make the call and get the return items
        try:
	    funcreturn = call(*args, **kwargs)
        except:
	    try:
		for i,a in enumerate(args):
 		    if isinstance(a, list):
		    	args[i] = np.array(args[i]).reshape(-1,1)
		    if isinstance(a, np.ndarray):
			args[i] = a.reshape(-1,1)
		funcreturn = call(*args, **kwargs)
	    except:
		for i, a in enumerate(args):
		    if isinstance(a,list):
			args[i] = np.array(args[i]).reshape(1,-1)
		funcreturn = call(*args, **kwargs)
	
	pdata = cPickle.dumps(funcreturn, cPickle.HIGHEST_PROTOCOL)
	#datahashvalues = '{}_{}'.format(time.time(), funcreturn)
	datahash = hashlib.sha256(pdata).hexdigest()
	insertrow = UserPyObj(g.user.id, pdata, method, datahash=datahash)
	db.session.add(insertrow)
	db.session.commit() 
	
	#Extract the response (attributes) from the function return and assign href for each
	try:
	    attributes = inspect.getmembers(funcreturn, lambda a:not(inspect.isroutine(a)))
	    publicattributes = [a for a in attributes if not (a[0].startswith('_') and a[0].startswith('__'))]
	except:
	    pass
	
	#Build the response
	response['data'] = {}
	for a in publicattributes:
	    response['data'][a[0]] = {'type':'{}'.format(type(a[1])), 'href':basedataurl + '/mydata/{}/{}'.format(datahash,a[0])}
	response['data']['full_results'] = {'type':'obj', 'href':basedataurl + '/mydata/{}/full'.format(datahash)}
	response['data']['raw'] = {'type':'python_object', 'href':basedataurl + '/mydata/{}/raw'.format(datahash)}
	return response


def recursedict(inputdict):
    #TODO: Make recursive - once I understand the PMD structure
    for k, v in inputdict.iteritems():
        if k == 'meta_data':
            newpositionalvalues = []
            oldpositionalvalues = v['positional_values']

            for i in oldpositionalvalues:
                if isinstance(i, np.ndarray):
                    newpositionalvalues.append(i.tolist())
                elif isinstance(i, ps.W):
                    newpositionalvalues.append(i.__repr__())
                else:
                    newpositionalvalues.append(i)

            v['positional_values'] = newpositionalvalues

        elif isinstance(v, np.ndarray):
            inputdict[k] = v.tolist()
        elif isinstance(v, ps.W):
            inputdict[k] = v.__repr__()

    return inputdict


def get_docs(module, method, module2=None):
    """
    Query the API to get the doc string of the method
    """
    response = {'status':'success','data':{}}
    response['data'] = []

    #Extract the method from the method dict
    if module2 == None:
        method = libraryfunctions[module][method]
    else:
        method = libraryfunctions[module][module2][method]

    #Introspect the docs
    docs = inspect.getdoc(method)
    for l in docs.split('\n'):
        response['data'].append(l)
    return response

def get_method(module, method, module2 = None):
    """
    Query the API to get the POST parameters.
    """
    if module2 == None:
        response = librarydocs[module][method]
    	response['doc_href'] = baseurl + '/api/{}/{}/docs/'.format(module, method)
    else:
        response = librarydocs[module][module2][method]
    	response['doc_href'] = baseurl + '/api/{}/{}/{}/docs/'.format(module, module2, method)
    return response
