from collections import Mapping
import copy
import os
import flask
from flask import Flask, jsonify, request, g, render_template, session,\
        redirect, url_for, escape, current_app
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
#from flask.ext.httpauth import HTTPBasicAuth

from app.mod_api.extractapi import recursive_extract, recursive_documentation

import config
from decorators import crossdomain

#TODO: Library name from config
ps = __import__(config.library)

#Create the app
app = Flask(__name__)
app.debug = config.DEBUG

#Create the login manager
lm = LoginManager(app)

#Add a class_references attribute to the application
with app.app_context():
    if getattr(current_app, 'class_references',None) is None:
        current_app.class_references = {}
seen_classes = set()  # Geom tables already mapped

#Configure the application from config.py
app.config.from_object('config')


#Define the database to  be used by
db = SQLAlchemy(app)

#Setup a fixed length dict to store cached objs
#TODO: Write a fixed length dict. by subclassing OrderedDict
cachedobjs = {}

#Initialize a listing of the library functionality
"""
The idea here is that pysalfunctions could be swapped
to be a JSON file or the underlying logic can change.

The only requirement is that this is a dictionary with
a most nested level of 'function_name':func_object pairs.
"""


def treeZip(t1,t2, path=[]):
    if isinstance(t1,Mapping) and isinstance(t2,Mapping):
        assert set(t1)==set(t2)
        for k,v1 in t1.items():
            v2 = t2[k]
            for tuple in treeZip(v1,v2, path=path+[k]):
                yield tuple
    else:
        yield (path, (t1,t2))

def setInDict(dataDict, mapList, value):
    getFromDict(dataDict, mapList[:-1]).pop(value, None)
def getFromDict(dataDict, mapList):
    return reduce(lambda d, k: d[k], mapList, dataDict)

def walk_dict(d):
    for k,v in d.items():
        if isinstance(v, dict):
            walk_dict(v)
        else:
            d[k] = True

def clean_empty(d):
    for k, v in d.items():
    	if isinstance(v,dict):
   	    if not v:
	    	d.pop(k, None)
	    else:
  		clean_empty(v)

visited = set([])
libraryfunctions = {}
recursive_extract(ps, libraryfunctions, ps.__name__, visited)

#ps specific
import w_from_geojson
libraryfunctions['weights']['queen_from_geojson'] = w_from_geojson.queen_geojson

#Recursive function extraction
librarydocs = copy.deepcopy(libraryfunctions)
recursive_documentation(librarydocs)

if config.generatemap:
    mapping = copy.deepcopy(libraryfunctions)
    walk_dict(mapping)
    import json
    with open('librarymap.json', 'w') as mapfile:
        mapfile.write(json.dumps(mapping, indent=2))

if config.loadmap:
    import json
    with open(config.loadmap, 'r') as configin:
	mapping = json.load(configin)
    livekeys = list(treeZip(libraryfunctions, mapping))
    for k, v in livekeys:
        if v[1] == False:
	    dataDict = setInDict(libraryfunctions, k, k[-1])
    clean_empty(libraryfunctions)
    clean_empty(libraryfunctions)

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

'''
from app.mod_user.models import User
auth = HTTPBasicAuth()
@auth.verify_password
def verify_password(username_or_token, password):
    user = User.verify_auth_token(username_or_token)
    if not user:
        user = User.query.filter_by(email=username_or_token).first()
        if not user or not user.verifypwd(password):
            return False
    g.user = user
    return True

#Error handling routed
@app.errorhandler(404)
def not_found(error):
    return "Error 404: Unable to find endpoint."
'''

#Home
@app.route('/', methods=['GET'])
def api_root():
    response = {'status':'success'}
    response['links'] = [{'id':'api', 'href': config.baseurl + '/api/', 'description':'Access to the PySAL API'},
                                 {'id':'user', 'href': config.baseurl + '/user/', 'description':'Login, Registration, and User management'}]
    return jsonify(response)

@app.after_request
def add_cors(resp):
    """ Ensure all responses have the CORS headers. This ensures any failures are also accessible
        by the client. """
    resp.headers['Access-Control-Allow-Origin'] = flask.request.headers.get('Origin','*')
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET'
    resp.headers['Access-Control-Allow-Headers'] = flask.request.headers.get(
        'Access-Control-Request-Headers', 'Authorization')
    # set low for debugging
    if app.debug:
        resp.headers['Access-Control-Max-Age'] = '86400'
    return resp

@app.before_request
def before():
    pass
###Import components use a blue_print handler###
#API
from app.mod_api.controllers import mod_api as api_module
app.register_blueprint(api_module, url_prefix='/api')

#User Management
from app.mod_user.controllers import mod_user as user_module
users = app.register_blueprint(user_module, url_prefix='/user')

#Data
from app.mod_data.controllers import mod_data as data_module
app.register_blueprint(data_module, url_prefix='/mydata')

#Uploads
#from app.mod_upload.controllers import mod_upload as upload_module
#app.register_blueprint(upload_module, url_prefix='/upload')

#Create the tables if this is a new deployment
db.create_all()
