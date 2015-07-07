import cPickle
import hashlib
import inspect
import numpy as np

from api_helpers import getargorder, gettoken

from flask import Blueprint, request, jsonify, g
from flask.ext.login import login_required, current_user
from config import baseurl
from app import  db, libraryfunctions, librarydocs, lm
from app.mod_data.models import UserPyObj
from config import baseurl, basedataurl

mod_api = Blueprint('mod_api', __name__)

def getfromdict(dataDict, mapList):
    return reduce(lambda d, k: d[k], mapList, dataDict)

@mod_api.route('/', methods=['GET'])
@login_required
def get_api():
    """
    The api homepage.
    """
    response = {'status':'success','links':[]}

    toplevel = libraryfunctions.keys()
    for i in toplevel:
        response['links'].append({'name':'{}'.format(i), 'href':baseurl + '/api/{}/'.format( i)})
    return jsonify(response)

@mod_api.route('/<module>/', methods=['GET'])
@login_required
def get_modules(module):
    """
    Modules within the
    """
    methods = libraryfunctions[module].keys()
    response = {'status':'success','links':[]}
    for i in methods:
        response['links'].append({'name':'{}'.format(i),
                                          'href':baseurl + '/api/{}/{}/'.format(module,i)})
    return jsonify(response)

@mod_api.route('/<module>/<path:remainder>/docs/', methods=['GET'])
@login_required
def getdocs(module, remainder):
    path = [module] + remainder.split('/')
    method = getfromdict(libraryfunctions, path)
    docs = inspect.getdoc(method)

    response = {'status':'success','data':{}}
    response['data'] = []

    for l in docs.split('\n'):
        response['data'].append(l)
    return jsonify(response)

def get_path(module, remainder):
    """
    Given a module and a remainder, return the path (dict keys).
    """
    return [module] + remainder.split('/')

def get_docs_or_tree(path, module, remainder):
    response = getfromdict(librarydocs, path)
    if 'doc_href' in response.keys():
        response['doc_href'] = '/api/{}/{}/docs'.format(module, remainder)
	#response['aggregate'] = '/api/{}/{}/aggregate/'.format(module, remainder)
    else:
        #This is not a terminal node
        links = []
        for k in response.keys():
	    href = '{}/api/{}/{}/{}/'.format(baseurl, module, remainder, k)
	    links.append({'name':k,
		      'href':href})
        response = {'status':'success', 'links':links}
    return response

@mod_api.route('/<module>/<path:remainder>/aggregate/', methods=['GET', 'POST'])
@login_required
def get_method_aggregate(module, remainder):
    path = get_path(module, remainder)
    if request.method == 'GET':
	response = get_docs_or_tree(path, module, remainder)

	#Clean the endpoint for the aggregator
	response.pop('doc_href', None)
	response.pop('aggregate', None)

	rp = response['parameters']['arguments']
	rp['iterable'] = {'chain_name':'iterable_href',
			  'description':'array of iterables inputs for some parameter(s)',
			  'type': 'array'}
	rp['iterable_arguments'] = {'chain_name':'iterable_arguments_href',
				    'description':'array of iterables identifying which parameters are iterating',
				    'type':'array'}
	response['name'] = response['name'] + ' Aggregator'
	return jsonify(response)
    elif request.method == 'POST':
	pass	


 
@mod_api.route('/<module>/<path:remainder>/', methods=['GET', 'POST'])
@login_required
def getmethod(module, remainder):
    path = get_path(module, remainder)
    if request.method == 'GET':
	response = get_docs_or_tree(path, module, remainder)
        return jsonify(response)

    elif request.method == 'POST':
        if not request.json:
            response = {'status':'error','data':{}}
            response['data'] = 'Post datatype was not json'
            return jsonify(response), 400
	else:
	    req = request.json
        #Request is well formatted
        response = {'status':'success','data':{}}
        call = getfromdict(libraryfunctions, path)

        if not 'arguments' in req.keys():
            print 'Error'
        postarguments = req['arguments']
	
        #Iterate over the arguments that are required and extract them.
        args = []
        argorder = getargorder(call)
        for a in argorder:
            #Check if the arg is a URL or raw data
            try:
                v = postarguments[a]
            except:
                a_key = '{}_href'.format(a)
                v = postarguments[a_key]
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

        kwargs = {}
        for k, v in postarguments.iteritems():
            #Skip arguments that do not have defaults, handled above
            if k in argorder:
                continue
            if '_href' in k and k.split('_')[0] in argorder:
                continue

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

	    #Explicit duck typing - this is pysal specific...
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
        insertrow = UserPyObj(current_user.get_id(), pdata, path[-1], datahash=datahash)
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
        return jsonify(response)

"""
TESTING AGGREGATION BELOW
"""

aggregator_docs = {"description": "An aggregation function for processing other functions",
		   "doc_href":"None",
		   "methods":["GET", "POST"],
		   "name":"aggregator",
		   "parameters":{"arguments":{
			"function":{'chain_name':'function_href',
				    'description':'The endpoint to iterate.',
				    'type':'function'},
			"iterable":{'chain_name':'iterable_href',
				    'description':'An array (of arrays) of parameters to be iterated.',
				    'type':'array'}, 
			"iterable_argument":{'chain_name':'iterable_argument_href',
					     'description':'Argument names mapped to the iterables argument',
					     'type':'array'}},
		   "server":[]},
		   "status":"success"}

@mod_api.route('/custom/aggregator/', methods=['GET', 'POST'])
@login_required
def aggregator():
    if request.method == 'GET':
	return jsonify(aggregator_docs)
    else:
	pseudocode = """
1. Verify JSON request
2. Extract the iterable function
3. Match the iterable request to arguments in the function (validation)
4. Use itertools.product to generate a request object
5. Execute each parameter set and aggregate the results
 """
	return pseudocode
