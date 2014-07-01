import ast
import inspect
import os

import numpy as np

from flask import Flask, render_template, jsonify, request, g
from flask.ext.restful import Api, Resource
from werkzeug.utils import secure_filename

from api import checktypes, funcs, CustomJsonEncoder

#Make the Flask App
app = Flask(__name__)
api = Api(app)

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
    response['data']['href'] = {'api':'/api/',
                                'uploaddata':'/upload/'}
    return jsonify(response)

@app.route('/api/<module>/', methods=['GET'])
def get_modules(module):
    methods = funcs[module].keys()
    response = {'status':'success','data':{}}
    response['data']['methods'] = []
    for i in methods:
        response['data']['methods'].append({i:'/api/{}/{}/'.format(module,i)})
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

    response['data']['documentation'] = '{}/{}/docs/'.format(module, mname)
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
    if not request.json:
        response = {'status':'error','data':{}}
        standarderror['data'] = 'Post datatype was not json'
        return jsonify(standarderror), 400
    else:
        response = {'status':'success','data':{}}

        #Setup the call, the args and the kwargs
        call = funcs[module][method]
        args = request.json['args']
        kwargs = request.json['kwargs']

        func_return = call(args, kwargs)

        response['data'] = request.json

        return jsonify(response)

#This is not API - can I abstract away and have this in the front-end?
@app.route('/upload/', methods=['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
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
                            'uploadmethod':'POST',
                            'template':{
                                'uploadfile':'Array of file(s) to upload'},
                        'uploadedfiles':files
                            }
                    }
        return jsonify(response)


#Replace with @app.route or swap over to API style - not both.
class UserAPI(Resource):
    def get(self):
        try:
            toplevel = funcs.keys()
            response = standardsuccess
            response['data']['modules'] = []
            for i in toplevel:
                response['data']['modules'].append({i:'/api/{}'.format(i)})
            return jsonify(response)
        except:
            response = standarderror
            response['data'] = 'Unable to load module list'
            return jsonify(response)
api.add_resource(UserAPI, '/api/', endpoint='api')

if __name__ == '__main__':
    app.config.update(DEBUG=True)
    app.run()
