import cPickle
import hashlib
import inspect
import numpy as np

from api_helpers import getargorder, gettoken

from flask import Blueprint, request, jsonify, g
from flask.ext.login import login_required
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
        response['links'].append({'id':'{}'.format(i), 'href':baseurl + '/api/{}'.format( i)})
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
        response['links'].append({'id':'{}'.format(i),
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

@mod_api.route('/<module>/<path:remainder>/', methods=['GET', 'POST'])
@login_required
def getmethod(module, remainder):
    path = [module] + remainder.split('/')
    if request.method == 'GET':
        response = getfromdict(librarydocs, path)
        response['doc_href'] = '/api/{}/{}/docs'.format(module, remainder)
        return jsonify(response)

    elif request.method == 'POST':
        if not request.json:
            response = {'status':'error','data':{}}
            response['data'] = 'Post datatype was not json'
            return jsonify(response), 400

        #Request is well formatted
        response = {'status':'success','data':{}}
        call = getfromdict(libraryfunctions, path)

        req = request.json
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
        insertrow = UserPyObj(g.user.id, pdata, path[-1], datahash=datahash)
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
