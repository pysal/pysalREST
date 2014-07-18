from collections import defaultdict
import ast
import inspect
import os
import json
import subprocess
import zipfile

import numpy as np
from pandas.io.json import read_json


from flask import Flask, render_template, jsonify, request, g

from werkzeug.utils import secure_filename

from api import checktypes, funcs, CustomJsonEncoder

#Make the Flask App
app = Flask(__name__)
#Setup a cache to store transient python objects

#Upload Setup
#TODO: Add a try/except here - if spatiallite is availabe, use it...
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['shp', 'dbf', 'shx', 'prj', 'zip'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

def unzip(filename, path):
    with zipfile.ZipFile(filename) as zf:
        for m in zf.infolist():
            words = m.filename.split('/')
            destination = path
            for w in words[:-1]:
                drive, w = os.path.splitdrive(w)
                head, w = os.path.split(w)
                if w in (os.curdir, os.pardir, ''):
                    continue
                destination = os.path.join(path, w)
            zf.extract(m, destination)
    return

@app.route('/', methods=['GET'])
def home():
    response = {'status':'success','data':{}}
    response['data']['links'] = [{'id':'api', 'href':'/api/'},
                                 {'id':'listdata', 'href':'/listdata/'},
                                 {'id':'upload', 'href':'/upload/'}]
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

        response['data'] = funcreturn

        return jsonify(response)


#This is not API - can I abstract away and have this in the front-end?
@app.route('/upload/', methods=['POST'])
def upload_file():
    """
    POST - Upload a file to the server (a directory)

    Examples:
    curl -X POST -F filename=@NAT.zip http://localhost:8081/upload/
    curl -X POST -F shp=@columbus.shp -F shx=@columbus.shx -F dbf=@columbus.dbf http:/localhost:8081/upload/
    """
    if request.method == 'POST':
        files = request.files
        uploaded = []
        for f in request.files.itervalues():
            uploaded.append(f)
            #Discard the keys - are they ever important since the user
            # has named the file prior to upload?
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                savepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(savepath)
                if filename.split('.')[1] == 'zip':
                    unzip(savepath, app.config['UPLOAD_FOLDER'])

        #Ideally we store metadata about the upload, but for now just return
        response = {'status':'success','data':{}}
        for u in uploaded:
            response['data'][u.filename] = '{}/{}'.format(app.config['UPLOAD_FOLDER'], u.filename)
        return jsonify(response)

    else:
        response = {'status':'error','data':{'message':'Either "." not in filename or extensions not in approved list.'}}
        return jsonify(response)
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
