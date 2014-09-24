from flask import Flask, jsonify, request, g, render_template, session, redirect, url_for, escape
from flask.ext.sqlalchemy import SQLAlchemy

#Create the app
app = Flask(__name__)

#Configure the application from config.py
app.config.from_object('config')

#Define the database to  be used by everyone


