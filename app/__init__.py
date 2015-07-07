from collections import Mapping
import copy
import os
import flask
from flask import Flask, jsonify, request, g, render_template, session,\
        redirect, url_for, escape, current_app
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager

from app.mod_api.extractapi import recursive_extract, recursive_documentation
import app.mod_api.aggregate as agg

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
    """
    Compare two dictionaries, updating t2 with key missing from
    t1.
    """

    if isinstance(t1, dict) and isinstance(t2, dict):
        try:
            assert(t1.keys() == t2.keys())
        except AssertionError:
            current_keys = set(t1.keys())
            mapped_keys = set(t2.keys())
            for k in current_keys.difference(mapped_keys):
                t2[k] = 'True'
    if isinstance(t1,Mapping) and isinstance(t2,Mapping):
        #assert set(t1)==set(t2)
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

if config.loadmap:
    import json
    with open(config.loadmap, 'r') as configin:
	mapping = json.load(configin)
        
    livekeys = list(treeZip(libraryfunctions, mapping))
    
    #livekeys is updated with potential new entries and rewritten, keeping existing settings
    with open('librarymap.json', 'w') as mapfile:
	mapfile.write(json.dumps(mapping, indent=2)) 

    for k, v in livekeys:
        if v[1] == False:
	    dataDict = setInDict(libraryfunctions, k, k[-1])
	    dataDict = setInDict(librarydocs, k, k[-1])

    #How can I better recursively clean?
    for x in range(4):
    	clean_empty(libraryfunctions)
    	clean_empty(librarydocs)

#Add in the custom aggregator
libraryfunctions['custom'] = {}
libraryfunctions['custom']['aggregator'] = agg.aggregator
librarydocs['custom'] = {}
librarydocs['custom']['aggregator'] = agg.aggregator_docs

print libraryfunctions.keys()

@lm.user_loader
def load_user(id):
    #Lazy load to avoid cylical imports
    from app.mod_user.models import User
    return User.query.get(int(id))

#Error handling routed
@app.errorhandler(404)
def not_found(error):
    return "Error 404: Unable to find endpoint."

#Home
@app.route('/', methods=['GET'])
def api_root():
    response = {'status':'success'}
    response['links'] = [{'name':'api', 'href': config.baseurl + '/api/', 'description':'Access to the PySAL API'},
                                 {'name':'user', 'href': config.baseurl + '/user/', 'description':'Login, Registration, and User management'}]
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
#from app.mod_data.controllers import mod_data as data_module
#app.register_blueprint(data_module, url_prefix='/mydata')

#Uploads
#from app.mod_upload.controllers import mod_upload as upload_module
#app.register_blueprint(upload_module, url_prefix='/upload')

#Create the tables if this is a new deployment
db.create_all()
