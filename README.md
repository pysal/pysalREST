pysalREST
=========

Assuming that you have PySAL installed via conda or pip:

python -m launcher --server cherry --api=pysail

In a browser:

0.0.0.0:8080/api/get

This returns an error (for now) due to the issue below.

Issues
=======

Serialization of some of the python objects in PySAL is not working.  So this is a broken example.  Everything we might return must be pickable so that json can be used to dump it.


