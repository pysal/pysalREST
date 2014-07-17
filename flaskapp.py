from collections import defaultdict
import ast
import inspect
import os
import json

import numpy as np
from pandas.io.json import read_json


from flask import Flask, render_template, jsonify, request, g
from flask.ext.cache import Cache

from werkzeug.utils import secure_filename

from api import checktypes, funcs, CustomJsonEncoder

#Make the Flask App
app = Flask(__name__)
#Setup a cache to store transient python objects
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

#Upload Setup
#TODO: Add a try/except here - if spatiallite is availabe, use it...
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['shp', 'dbf', 'shx', 'prj'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

#standardsuccess = {'status':'success','data':{}}
#standarderror = {'status':'error','data':{}}
#standardfail = {'status':'fail','data':{}}


@app.route('/', methods=['GET'])
def home():
    response = {'status':'success','data':{}}
    response['data']['links'] = [{'id':'api', 'href':'/api/'},
                                 {'id':'listdata', 'href':'/listdata/'},
                                 {'id':'uploaddata', 'href':'/uploaddata/'}]
    return jsonify(response)

@app.route('/api/<module>/', methods=['GET'])
def get_modules(module):
    methods = funcs[module].keys()
    response = {'status':'success','data':{}}
    response['data']['links'] = []
    for i in methods:
        response['data']['links'].append({'id':'{}'.format(i),
                                          'href':'/api/{}/{}/'.format(module,i)})
    return jsonify(response)

@app.route('/api/<module>/<method>/', methods=['GET'])
def get_method(module, method):
    """
    Query the API to get the POST parameters.
    """
    #Setup the response strings
    response = {'status':'success','data':{}}
    response['data']['post_template'] = {}
    mname = method
    #Extract the method from the method dict
    method = funcs[module][method]

    #Inspect the method to get the arguments
    try:
        reqargs = inspect.getargspec(method)
    except:
        reqargs = inspect.getargspec(method.__init__)

    args = reqargs.args
    defaults = list(reqargs.defaults)
    try:
        args.remove('self')
    except:
        pass

    #Pack the arguments into the pos_template
    response['data']['post_template'] = {'args':[], 'kwargs':{}}
    diff = len(defaults) - len(args)
    for i, arg in enumerate(args):
        if diff < 0:
            diff += 1
            response['data']['post_template']['args'].append(arg)
        else:
            response['data']['post_template']['kwargs'][arg] = defaults[diff]

    response['data']['links'] = {'id':'docs',
                                 'href':'{}/{}/docs/'.format(module, mname)}
    return jsonify(response)

@app.route('/api/<module>/<method>/docs/', methods=['GET'])
def get_docs(module, method):
    """
    Query the API to get the doc string of the method
    """
    response = {'status':'success','data':{}}
    response['data']['docstring'] = []

    #Extract the method from the method dict
    method = funcs[module][method]

    #Introspect the docs
    docs = inspect.getdoc(method)
    for l in docs.split('\n'):
        response['data']['docstring'].append(l)
    return jsonify(response)


@app.route('/api/<module>/<method>/', methods=['POST'])
def post_region(module,method):
    """
    To make a POST using CURL to the flask dev server:
    Fisher-Jenks using the Hartigan Olympic time example
    curl -i -H "Content-Type: application/json" -X POST -d '{"args":["[12, 10.8, 11, 10.8, 10.8, 10.6, 10.8, 10.3, 10.3,10.3,10.4,10.5,10.2,10.0,9.9]"], "kwargs":{"k":5}}' http://localhost:5000/ap/esda/fisher_jenks/
    or
    Sample Jenks Caspall using the same example - note that sample
     percentage is not passed.
    curl -i -H "Content-Type: application/json" -X POST -d '{"args":["[12, 10.8, 11, 10.8, 10.8, 10.6, 10.8, 10.3, 10.3,10.3,10.4,10.5,10.2,10.0,9.9]"], "kwargs":{"k":5}}'  http://localhost:5000/ai/esda/jenks_caspall_sampled/
    """
    if not request.json:
        response = {'status':'error','data':{}}
        standarderror['data'] = 'Post datatype was not json'
        return jsonify(standarderror), 400
    else:
        response = {'status':'success','data':{}}

        #Setup the call, the args and the kwargs
        call = funcs[module][method]

        #Parse the args
        args = request.json['args']
        print type(args)
        validargs = []
        for a in args:
            #Literal eval to get the native python type
            va = json.loads(a)
            #va = ast.literal_eval(a)
            #If it is a list, cast to a numpy ndarray via pandas json io
            #This should go to a decorator on the PySAL side at some point
            if isinstance(va, list):
                va = read_json(a)
            validargs.append(va.values.ravel())

        #Check for and parse the kwargs
        try:
            kwargs = request.json['kwargs']
            validkwargs = {}
            validkwargs = ast.literal_eval(str(kwargs))
        except:
            pass

        #Make the call and get the return items
        funcreturn = vars(call(*validargs, **validkwargs))
        for k, v in funcreturn.iteritems():
            if isinstance(v, np.ndarray):
                funcreturn[k] = v.tolist()
            elif isinstance(v, ps.W):
                print "W OBJ"

        response['data'] = funcreturn

        return jsonify(response)

def make_cache_key():
    print "Generating key!"

@cache.cached(timeout=None, key_prefix=make_cache_key)
def cacheW(w):
    """
    Cache the W object since we need it throughout PySAL
    """
    return w


#This is not API - can I abstract away and have this in the front-end?
@app.route('/upload/', methods=['PUT', 'GET'])
def upload_file():
    """
    GET - An altertive method to list the files on the server
          and get the PUT parameter format

    PUT - Upload a file to the server (a directory)
    """
    if request.method == 'PUT':
        print request.json
        f = request.files['uploadfile']
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return 'success'
        else:
            response = {'status':'error','data':{'message':'Either "." not in filename or extensions not in approved list.'}}
            return jsonify(response)

    elif request.method == 'GET':
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        #TODO: Maybe key these by name and then have an array of components?
        response = {'status':'success',
                    'data':{
                            'uploadmethod':'PUT',
                            'template':{
                                'uploadfile':'Array of file(s) to upload'},
                        'uploadedfiles':files
                            }
                    }
        return jsonify(response)


@app.route('/api/', methods=['GET'])
def get_api():
    """
    The api start page.
    """
    response = {'status':'success','data':{}}
    response['data']['links'] = []

    toplevel = funcs.keys()
    for i in toplevel:
        response['data']['links'].append({'id':'{}'.format(i), 'href':'/api/{}'.format( i)})
    return jsonify(response)

@app.route('/listdata/', methods=['GET'])
def get_listdata():
    """
    List the data that is in the upload directory
    """
    response = {'status':'success','data':{}}
    files = {}
    for f in os.listdir(UPLOAD_FOLDER):
        basename = f.split('.')[0]
        if basename not in files.keys():
            files[basename] = []
            files[basename].append(os.path.join(UPLOAD_FOLDER, f))
        else:
            files[basename].append(os.path.join(UPLOAD_FOLDER, f))
    response['data']['files'] = files
    return jsonify(response)

if __name__ == '__main__':
    app.config.update(DEBUG=True)
    app.run()
