pysalREST
=========

Assuming that you have PySAL installed via conda or pip:

python -m launcher --server cherry --api=pysalrest

GET Request:
------------

Listing supported functions
+++++++++++++++++++++++++++

`0.0.0.0:8080/api/api/`

Generating a W using the canned example
+++++++++++++++++++++++++++++++++++++++

`http://localhost:8080/api/api/queen_from_shapefile?args=['columbus.shp']`

POST Request:
-------------

This uses curl and is a canned example using Fisher Jenks to classify the Hartigan Olympic  running times.

`curl -d func='Fisher_Jenks' -d args='[12, 10.8, 11, 10.8, 10.8, 10.6, 10.8, 10.3, 10.3,10.3,10.4,10.5,10.2,10.0,9.9], 5' -X POST 'localhost:8080/api/api'`

Issues
=======

Serialization of some of the python objects in PySAL is not working.  


