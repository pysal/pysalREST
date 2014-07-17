pysalREST
=========
PySALREST can be launched in three ways:

1. Using the lightweight flask server (development server):

`python flaskapp.py`

The base URL is not localhost:5000

2. Using CherryPy (Midweight Server)

`launcher -m --server cherry --api=pysalrest --port 8081`

It is safe to omit the port flag if not services run on 8081.  The default is 8080.  Yielding a base URL of localhost:8080

3. Behind Apache as a WSGI.



POST Request:
-------------

This uses curl and is a canned example using Fisher Jenks to classify the Hartigan Olympic  running times.
 
`curl -i -H "Content-Type: application/json" -X POST -d '{"args":["[12, 10.8, 11, 10.8, 10.8, 10.6, 10.8, 10.3, 10.3,10.3,10.4,10.5,10.2,10.0,9.9]"], "kwargs":{"k":5}}' http://localhost:5000/api/esda/fisher_jenks/`



