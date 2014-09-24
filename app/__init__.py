from flask import Flask, jsonify, request, g, render_template, session, redirect, url_for, escape
from flask.ext.sqlalchemy import SQLAlchemy

from app.mod_api.extractapi import extract
import pysal as ps

#Create the app
app = Flask(__name__)

#Configure the application from config.py
app.config.from_object('config')

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

'''
@app.errorhandler(404)
def not_found(error):
    return "Error 404: Unable to find endpoint."
'''
###Import components use a blue_print handler###

#API
from app.mod_api.controllers import mod_api as api_module
app.register_blueprint(api_module, url_prefix='/api')

#Login

#Database
