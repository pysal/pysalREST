import ast
import decimal
import glob
import hashlib
import os
import shutil
import subprocess
import tempfile
import time

import numpy as np

from flask import Blueprint, request, jsonify, g, current_app
from werkzeug.utils import secure_filename

import geoalchemy2.functions as geofuncs

from app import auth, db, seen_classes, cachedobjs
from app.mod_data.models import UserData, UserPyObj, GeoPoly, GEOMLOOKUP
from app.mod_upload import upload_helpers as uph
import config

mod_upload = Blueprint('mod_upload', __name__)

@mod_upload.route('/', methods=['GET'])
@auth.login_required
def upload_get():
    """
    The upload homepage.
    """
    response = {'status':'success','data':{}}
    return jsonify(response)

@mod_upload.route('/', methods=['POST'])
@auth.login_required
def upload():
    """
    Upload to a temporary directory, validate, call ogr2ogr and write to the DB

    Using curl via the command line.
    ---------------------------------
    Example 1 is from pysal examples (from that dir)
    Example 2 is a subset of NAT, zipped.
    Example 3 is columbus via the webpool and a sample user.
    curl -X POST -F shp=@columbus.shp -F shx=@columbus.shx -F dbf=@columbus.dbf http://localhost:8080/mydata/upload/
    curl -X POST -F filename=@NAT_Subset.zip http://localhost:8080/mydata/upload/
    curl -i -k -u jay@jay.com:jay -X POST -F filename=@col.zip  https://webpool.csf.asu.edu/pysalrest/mydata/upload/
    """
    if hasattr(g.user, 'tmpdir'):    
        tmpdir = g.user.tmpdir
    else:
        tmpdir = tempfile.mkdtemp()
        g.user.tmpdir = tmpdir
    cuid = g.user.id
    for f in request.files.values():
        if f and uph.allowed_file(f.filename):
            filename = secure_filename(f.filename)
            savepath = os.path.join(tmpdir, filename)
            f.save(savepath)

            basename, ext = filename.split('.')
            if ext == 'zip':
                uph.unzip(savepath, tmpdir)

    #Now iterate over all the shapefiles and call ogr2ogr
    shps = glob.glob(os.path.join(tmpdir, '*.shp'))
    for shp in shps:
        shptablename = os.path.splitext(os.path.basename(shp))[0]
	datahashvalue = '{}_{}_{}'.format(cuid, shptablename, time.time())
	datahash = hashlib.md5(datahashvalue).hexdigest()

	host, port = config.dbhost.split(':')
        cmd = [config.ogr2ogr, '-f', "{}".format(config.dbtypename),
               "{}:host={} port={} user={} password={} dbname={}".format(config.dbabbrev,
                                                                 host,
                                                                 port,
                                                                 config.dbusername,
                                                                 config.dbpass,
                                                                 config.dbname),
               shp,
               '-nlt', 'PROMOTE_TO_MULTI',
               '-nln', datahash,
               '-lco', 'GEOMETRY_NAME={}'.format(config.geom_column),
		'-skipfailures']

        response = subprocess.call(cmd)

        uploadeddata = UserData(cuid, datahash, shptablename)
        db.session.add(uploadeddata)
        db.session.commit()

    #Cleanup
    shutil.rmtree(tmpdir)

    return jsonify({'status':'success', 'data':{'href':'mydata/{}'.format(datahash)}})
