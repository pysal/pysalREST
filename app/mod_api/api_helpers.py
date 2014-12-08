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
from app import pysalfunctions, db
from app.mod_data.models import UserPyObj

def getargorder(call):
    """
    Get the order of required args from a function. 
    Does not support *args currently.
    """
    try:
        argorder = inspect.getargspec(call)[0]
    except:
        argorder = inspect.getargspec(call.__init__)[0][1:]  #ignore self
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
    #TODO: This needs a refactor badly - handling python objs, etc.
    if not request.json:
        response = {'status':'error','data':{}}
        response['data'] = 'Post datatype was not json'
        return jsonify(response), 400
    else:
        response = {'status':'success','data':{}}
        #Setup the call, the args and the kwargs
        
	if module2 == None:
	    argorder = getargorder(pysalfunctions[module][method])
            call = pmdwrapper(pysalfunctions[module][method])
        else:
	    argorder = getargorder(pysalfunctions[module][module2][method])
            call = pmdwrapper(pysalfunctions[module][module2][method])

        #Parse the args
        keys = request.json.keys()
        req = request.json

        #Setup the python arg / kwarg containers
        args = []
        kwargs = {}
        if 'args' in keys:
	    for a in argorder:
		if a in req['args'].keys():
		    #Try to treat as a url, assuming tokenized input
		    value = req['args'][a]
		    value = gettoken(value)
                    if not value:
			value = req['args'][a]

	  	    if not a:
	    		return {'status':'failure', 'message':'Unable to get data from url: {}'.format(a)}
		    
		    #Try to cast the data to a python type
		    try:
			pythonarg = ast.literal_eval(value)
		    except:
			pythonarg = value
		    args.append(pythonarg)

		#An unexpected argument was provided
		else:		
		    print "Arg {} not found in inputs. Trying anyway".format(a)
        
	if 'kwargs' in keys:
            for k, v in req['kwargs'].iteritems():
		#Try to treat as a token
		value = v		
	  	value = gettoken(v)
		if not value:
               	    value = v
 
		#Try to cast the response to a json object
                try:
                    kwargs[k] =  ast.literal_eval(v)
                except:
                    kwargs[k] = v
        # or if they are uploaded shapefiles
        for i, a in enumerate(args):
            try:
                if a in UPLOADED_FILES:
                    args[i] = UPLOAD_FOLDER + '/' +  a
                    shpname = a.split('.')[0]
            except: pass
            try:
                if a.split('_')[0] == 'cached':
                    cacheid = a.split('_')[1]
		    #Get the object out of the DB
		    result = UserPyObj.query.filter_by(id = cacheid).first()
		    obj = cPickle.loads(str(result.pyobj))
                    args[i] = obj
            except: pass

	    if isinstance(a, list):
		arr = np.array(a)
		args[i] = np.array(a)

        for k, v in kwargs.iteritems():
            try:
                if v in UPLOADED_FILES:
                    kwargs[k] = os.path.join(UPLOAD_FOLDER, v)
            except: pass

            try:
                if v.split('_')[0] == 'cached':
                    cacheid = v.split('_')[1]
                    query = "SELECT Obj FROM WObj WHERE ID = {}".format(cacheid)
                    cur = get_db().cursor().execute(query)
                    result = cur.fetchone()[0]
                    obj = cPickle.loads(str(result))

                    kwargs[k] = obj
                    cur.close()
            except: pass


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
	datahashvalues = '{}_{}'.format(time.time(), funcreturn)
	datahash = hashlib.md5(datahashvalues).hexdigest()
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
	    response['data'][a[0]] = {'type':'{}'.format(type(a[1])), 'href':'mydata/{}/{}'.format(datahash,a[0])}
	response['data']['full_results'] = {'type':'obj', 'href':'mydata/{}/full'.format(datahash)}
	response['data']['raw'] = {'type':'python_object', 'href':'mydata/{}/raw'.format(datahash)}
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
    response['data']['docstring'] = []

    #Extract the method from the method dict
    if module2 == None:
        method = pysalfunctions[module][method]
    else:
        method = pysalfunctions[module][module2][method]

    #Introspect the docs
    docs = inspect.getdoc(method)
    for l in docs.split('\n'):
        response['data']['docstring'].append(l)
    return response

def get_method(module, method, module2 = None):
    """
    Query the API to get the POST parameters.
    """
    #Setup the response strings
    response = {'status':'success','data':{}}
    mname = method
    response['data']['name'] = mname
    response['data']['methods'] = ['GET', 'POST']
    #Extract the method from the method dict
    if module2 == None:
        method = pysalfunctions[module][method]
    else:
        method = pysalfunctions[module][module2][method]

    #Inspect the method to get the arguments
    try:
        reqargs = inspect.getargspec(method)
        classtype = False
    except:
        reqargs = inspect.getargspec(method.__init__)
        classtype = True

    docstring = inspect.getdoc(method)
    
    #Remove self and get defaults
    args = reqargs.args
    
    if reqargs.defaults != None:
        defaults = list(reqargs.defaults)
    else:
        defaults = []
    try:
        args.remove('self')
    except:
        pass
    #Parse the docstring for an argument type
    argtype = OrderedDict()
    doclist = docstring.split('\n')
    for a in args:
        argtype[a] = {'name': a, 'type':'Unknown', 'description':'None'}
        for i, l in enumerate(doclist):
            if re.match(r'\b{}\b'.format(a), l):
                intype = l.split(':')[-1]
                argtype[a]['type'] = intype.strip()
                desc = []
                j = 1
                while ':' not in doclist[i+j]:
                    if len(doclist[i+j]) == 0:
                        break
		
                    desc.append(doclist[i+j].strip() + ' ')
                    j += 1
		    if i + j >= len(doclist):
			break
                description = "".join(desc)
                argtype[a]['description'] = description
            if 'Attributes' in l:
                break
    #Pack the arguments into the post template
    response['data']['required_arguments'] = {}
    response['data']['optional_arguments'] = {}
    diff = len(defaults) - len(args)
    #TODO: Required args needs to be a dict.
    for i, arg in enumerate(argtype):
        if diff < 0:
            diff += 1
	    data = argtype[arg]
	    name = data['name']
	    data.pop('name', None)
	    data['chain_name'] = '{}_href'.format(name)
            response['data']['required_arguments'][name] = argtype[arg]
        else:
            default = defaults[diff]
            argtype[arg]['default'] = default
	    data = argtype[arg]
	    name = data['name']
	    data['chain_name'] = '{}_href'.format(name)
	    data.pop('name', None)
            response['data']['optional_arguments'][name] = data
            diff += 1
    response['data']['doc_href'] = '{}/{}/docs/'.format(module, mname)
    
    response['data']['response_template'] = {}
    if inspect.isclass(method):
	#Parse for Attributes in the doc string
	inattributes = False
	for i, l in enumerate(doclist):
	    if 'Attribute' in l:
		inattributes = True
	    if inattributes:
		if ':' in l:
		    j = 1
		    line = l.split(':')
		    name = line[0].strip()
		    type = line[1].strip()
      		    desc = []
		    if i + j > len(doclist):
			continue
                        if len(doclist[i+j]) == 0:
                            break
                        desc.append(doclist[i+j].strip() + ' ')
                        j += 1
			if i+j >= len(doclist):
			    break
		    description = "".join(desc)
		    response['data']['response_template'][name] =  {'type':type, 'description':description, 'chain_href':'{}_href'.format(name)}
	
    else:
    	response['data']['response_template'] = []
    	#Parse for Returns in the docstring 
	inreturns = False
	for i, l in enumerate(doclist):
	    if 'Returns' in l:
		inreturns = True
	    if inreturns:
		if ':' in l:
		    j=1
		    line = l.split(':')
		    name = line[0].strip()
		    type = line[1].strip()
		    desc = []
 		    if i + j >= len(doclist):
			continue
                    while ':' not in doclist[i+j]:
                        if len(doclist[i+j]) == 0:
                            break
                        desc.append(doclist[i+j].strip() + ' ')
                        j += 1
 			if i + j >= len(doclist):
				break
                    description = "".join(desc)
                    response['data']['response_template'].append({'name':name, 'type':type, 'description':description})
    methoddescription = []
    for l in doclist:
	if len(l) == 0:
	    break
	methoddescription.append(l.strip())

    response['data']['description'] = "".join(methoddescription)
    return response
