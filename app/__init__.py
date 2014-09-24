import os

from flask import Flask, jsonify, request, g, render_template, session, redirect, url_for, escape
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID

from app.mod_api.extractapi import extract
import pysal as ps
import config

#Create the app
app = Flask(__name__)

#Configure the application from config.py
app.config.from_object('config')

#Instantiate the login manager
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'mod_user.signin'
oid = OpenID(app, os.path.join(config.BASE_DIR, 'tmp'))

#Define the database to  be used by
db = SQLAlchemy(app)

#Initialize a listing of the PySAL functions
"""
The idea here is that pysalfunctions could be swapped
to be a JSON file or the underlying logic can change.

The only requirement is that this is a dictionary with
a most nested level of 'function_name':func_object pairs.
"""
pysalfunctions = extract(ps, {})

#Error handling routed
@app.errorhandler(404)
def not_found(error):
    return "Error 404: Unable to find endpoint."

#Home
@app.route('/', methods=['GET'])
def api_root():
    response = {'status':'success','data':{}}
    response['data']['links'] = [{'id':'api', 'href':'/api/'},
                                 {'id':'listdata', 'href':'/listdata/'},
                                 {'id':'upload', 'href':'/upload/'},
                                 {'id':'cached', 'href':'/cached/'}]
    return jsonify(response)

###Import components use a blue_print handler###

#API
from app.mod_api.controllers import mod_api as api_module
app.register_blueprint(api_module, url_prefix='/api')

#User Management
from app.mod_user.controllers import mod_user as user_module
app.register_blueprint(user_module, url_prefix='/user')

#Database


#Create the tables if this is a new deployment
db.create_all()
