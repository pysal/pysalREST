import os
import flask
from flask import Flask, jsonify, request, g, render_template, session,\
        redirect, url_for, escape, current_app
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.httpauth import HTTPBasicAuth

from app.mod_api.extractapi import extract
import config
from decorators import crossdomain

import pysal as ps

#Create the app
app = Flask(__name__)
app.debug = config.DEBUG
#app.wsgi_app = ReverseProxied(app.wsgi_app)

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

#Initialize a listing of the PySAL functions
"""
The idea here is that pysalfunctions could be swapped
to be a JSON file or the underlying logic can change.

The only requirement is that this is a dictionary with
a most nested level of 'function_name':func_object pairs.
"""
pysalfunctions = extract(ps, {})


from app.mod_user.models import User
auth = HTTPBasicAuth()
@auth.verify_password
def verify_password(username_or_token, password):
    print username_or_token
    user = User.verify_auth_token(username_or_token)
    if not user:
        user = User.query.filter_by(email=username_or_token).first()
        if not user or not user.verifypwd(password):
            return False
    g.user = user
    return True

'''
#Error handling routed
@app.errorhandler(404)
def not_found(error):
    return "Error 404: Unable to find endpoint."
'''

#Home
@app.route('/', methods=['GET'])
def api_root():
    response = {'status':'success','data':{}}
    response['data']['links'] = [{'id':'api', 'href':'/api/', 'description':'Access to the PySAL API'},
                                 {'id':'user', 'href':'/user/', 'description':'Login, Registration, and User management'},
                                 {'id':'data', 'href':'/data/', 'description':'Data, Upload, and Cached PyObject Items'}]
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
app.register_blueprint(data_module, url_prefix='/data')

#Create the tables if this is a new deployment
db.create_all()
