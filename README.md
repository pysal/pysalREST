pysalREST Sample Application
=============================
The repository contains a Vagrantfile for use with the Vagrant virtual machine management software.  This VM contains all of the necessary software dependencies (GDAL, Python via Anaconda, Fiona, etc.).  Installation takes ~20-30 minutes are the machine image is downloaded and all dependencies are installed.

Launcing the VM
-----------------
To launch the VM, simply execute `vagrant up` in the directory where pysalREST has been cloned.

Host-Only-Network
------------------
The VM sets up a NAT and a host only netowrk.  Port 8080 is forwarded from the guest to the host.  To connect to the server use localhost:8080.  To view the sample application use localhost:8080/index.html/

Launching the Sample Application
---------------------------------
The sample application **should** launch automatically when the VM has booted.  If it does not:

* `vagrant ssh` to ssh into the virtual machine
* `cd pysalREST` into the directory where pysalREST has been cloned.  In the default installation this is `~/pysalREST`
* `python -m launcher --server=cherry --api=pysalrest --port=8080` 

To connect to the sample application open a web browser on the host OS at localhost:8080/index.html.  Note: It is important to use localhost and not 127.0.0.1 due to some javascript origin issue.

pysalREST API
================
PySALREST can be launched in three ways:

1. Using the lightweight flask server (development server):

`python flaskapp.py`

The base URL is not localhost:5000

2. Using CherryPy (Midweight Server)

`python launcher -m --server cherry --api=pysalrest --port 8081`

It is safe to omit the port flag if not services run on 8081.  The default is 8080.  Yielding a base URL of localhost:8080

3. Behind Apache as a WSGI.

Navigation
-----------
The goal of the service is that it is machine discoverable.  Therefore, `href` tags will be scattered in with more human readable return information to support mapping the struture of the API.

For the human user:

 * `/api/` is the root access to the API.  From here all PySAL methods are available in the URL form `/api/module/method`.  The method endpoints can then be accessed via POST requests to call methods on some JSON provided arguments.  See POST Request for Method Calls, below.
 * `/listdata/` is a listing of the datasets which have been uploaded.  This is a flat file upload for now.  From here, all data information, inclusing feature geometries and attributes are accessible in the form `/listsdata/dataset/` and `listdata/dataset/field`.
 * `/upload/` is a POST only access point for uploading data.  See POST Request for File Uploads, below, for more information.
 *  `/cached/` is access to a sqlite database that stores Python class instance objects.  Currently this only supports the PySAL W Object.  Access takes the form of `/cached/id/` to access a listing of available attributes and methods.  Attributes can be accessd via a GET request to `/cached/id/attribute` and methods can be called on the object (which is then updated in the database) via a POST request to `/cached/id/method_name` with args sent as well formed JSON

POST Request for Method Calls:
-------------------------------

This uses curl and is a canned example using Fisher Jenks to classify the Hartigan Olympic  running times.
 
`curl -i -H "Content-Type: application/json" -X POST -d '{"args":["[12, 10.8, 11, 10.8, 10.8, 10.6, 10.8, 10.3, 10.3,10.3,10.4,10.5,10.2,10.0,9.9]"], "kwargs":{"k":5}}' http://localhost:5000/api/esda/fisher_jenks/`

POST Request for File Uploads:
-------------------------------
More curl examples for a single .zip and multiple shapfile components:

`curl -X POST -F filename=@NAT.zip http://localhost:8081/upload/`

`curl -X POST -F shp=@columbus.shp -F shx=@columbus.shx -F dbf=@columbus.dbf http:/localhost:8081/upload/`

POST Request to call a method on an object:
-------------------------------------------
Another curl example.  This example assumes that nothing has been uploaded.  Simply change the ID to point at the shapefile in the cache database if you have data uploaded.

1. Upload NAT: `curl -X POST -F filename=@NAT.zip http://localhost:5000/upload/`

2. Generate a W: `curl -i -H "Content-Type: application/json" -X POST -d '{"args":[NAT.shp]}' http://localhost:5000/api/weights/queen_from_shapefile/`

3. Row standardize the W: `curl -i -H "Content-Type: application/json" -X POST -d '{"args":["r"]}' http://localhost:5000/cached/1/set_transform/`  - This assumes that NAT is id=1.  Alter to the last DB entry if you have uploaded other shapefiles.

4. Check the standardization via the webbrowser: `http://localhost:5000/cached/1/weights/`

5. Revert to binary weights: `curl -i -H "Content-Type: application/json" -X POST -d '{"args":["b"]}' http://localhost:5000/cached/1/set_transform/`
 

