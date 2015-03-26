pysalREST
=============================
This repository contains an automated Python library extraction tool originally developed to expose the PySAL library as a RESTful service.  Conceptually, we sought to introspect the entirety of our code base and expose each function and class as a RESTful endpoint.  As the project evolved, we added the ability to interface with a server side database, ingest external data sources via HREFs, and curate the functionality to be exposed.

We leverage the Flask python microframework to create the RESTful service and cherrypy to run as either a lighweight production server or behind a traditional webserver such as Apache.

We make two assumptions about your library:

1. Your documentation conforms to the numpydoc specification: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
2. Your project does not wrap an existing C style library.  We see libraries such as GDAL, where a single class is the entry point to a majority of the functionality, as problematic using our approach.

Currently we impose a third limitation in the structure of the directories within your modules.  We have statically coded the logic to traverse two directory levels deep from the root.  Any functionality deeper is not exposed.  For example, we successfully expose all functionality in:

	-root
		-a
		-b
			-b1
		
but fail to expose all functionality from 1a1 in the following example.

	-root
		-a
			-a1
				-1a1
		-b
			-b1
		
In an upcoming PR we will replace all hard coded traversal with recursive traversal.

Configuration
-------------
Configuration occurs via the confi.py file.  This file is not accessible via the REST interface.  We expose the following via the configuration file:

General
________

* DEBUG - boolean defining whether debug messages should be logged
* THREADS\_PER\_PAGE - integer number of threads per connection
* SECRET\_KEY - your secret hash key
* ALLOWED\_EXTENSIONS - for the data service, only uploads with these extensions are accepted

* BASE\_DIR - current installation path, you should not need to change this

API
________


* library - the name of the module as you would use in an import statement, e.g. pysal
* api - the name of the api used in URLs
* generatemap - boolean defining whether a json map of the exposed functionality should be generated
* localmap - the name of a map to be lodaded to curate functionality

Server
________


* server - the name of the server to use, alter if you do not want to use cherrypy
* port - the port to run the server on
* host - the ip to run the server on, e.g. localhost

* APPLICATION\_ROOT - the base URL to be appended to all other URLs
* baseurl - the baseurl appened when generating hrefs in the API
* basedataurl - as above, except a base url to data

Database Setup
_________________


* dbtypename - an ogr2ogr specific parameter defining the database type; if you are not using ogr2ogr you can ignore
* dbabbrev - database abbreviation for ogr2ogr
* dbtype - used for SQLAlchemy mapping
* dbhost - address to the db
* dbusername - username with read/write priveleges
* dbpass - the dbusername's password
* dbname - the name of the database at the given address

* geom_column - in the case of a POSTGIS enabled database, this is the default geometry column name

3rd Party
__________


* ogr2ogr - PATH to the ogr2ogr command

Logging
________


* loglocation - PATH for logs

Running the server
------------------
For initial testing, we suggest running a localhost, cherrypy based server.  This allows for local testing of all endpoints.

To do this, modify config.py, setting the host parameter equal to localhost and the port to some currently unused port.  Finally, execute `python run.py`.

On run, pysalREST will introspect your code base and extraction documentation.  Classes and functions for which documentation extraction fails will print an error message to the terminal.