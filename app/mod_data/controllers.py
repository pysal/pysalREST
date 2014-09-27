import ast
import glob
import os
import subprocess
import tempfile

from flask import Blueprint, request, jsonify, g, current_app
from flask.ext.login import login_required, current_user
from werkzeug.utils import secure_filename

import geoalchemy2.functions as geofuncs

from app import db, seen_classes
from app.mod_data.models import UserData, UserPyObj, GeoPoly
from app.mod_data import upload_helpers as uph
import config

mod_data = Blueprint('mod_data', __name__)

@mod_data.route('/', methods=['GET'])
@login_required
def data():
    """
    The data homepage.
    """
    response = {'status':'success','data':{}}
    response['data']['links'] = [{'id':'listdata', 'href':'/listdata/'},
                                {'id':'upload', 'href':'/upload/'},
                                {'id':'cached', 'href':'/cached/'}]
    return jsonify(response)

@mod_data.route('/listdata/', methods=['GET'])
@login_required
def listdata():
    """
    List the available datasets by querying the DB and
    returning metadata about the available user uploaded data.
    """
    cuid = current_user.id
    response = {'status':'success','data':{}}
    availabledata = UserData.query.filter_by(userid = cuid).all()
    for a in availabledata:
        dataname = a.datahash.split('_')
        entry = {'dataname':dataname[1],
                'href':'/data/{}/{}'.format(cuid, a.datahash),
                'datecreated': a.date_created,
                'datemodified': a.date_modified}
        response['data'][a.id] = entry
    return jsonify(response)

@mod_data.route('/upload/', methods=['POST'])
#TODO: Turn on login here and remove static CUID.
#@login_required
def upload():
    """
    Upload to a temporary directory, validate, call ogr2ogr and write to the DB

    Using curl via the command line.
    ---------------------------------
    Example 1 is from pysal examples (from that dir)
    Example 2 is a subset of NAT, zipped.
    curl -X POST -F shp=@columbus.shp -F shx=@columbus.shx -F dbf=@columbus.dbf http://localhost:8080/data/upload/
    curl -X POST -F filename=@NAT_Subset.zip http://localhost:8080/data/upload/
    """
    tmpdir = tempfile.mkdtemp()
    cuid = 4
    #cuid = current_user.id

    for f in request.files.values():
        if f and uph.allowed_file(f.filename):
            filename = secure_filename(f.filename)
            savepath = os.path.join(tmpdir, filename)
            f.save(savepath)

            basename, ext = filename.split('.')
            print basename, ext
            if ext == 'zip':
                uph.unzip(savepath, tmpdir)

    #Now iterate over all the shapefiles and call ogr2ogr
    shps = glob.glob(os.path.join(tmpdir, '*.shp'))
    for shp in shps:
        shptablename = uph.hashname(shp, cuid)
        host, port = config.dbhost.split(':')
        cmd = [config.ogr2ogr, '-f', "{}".format(config.dbtypename),
               "{}:host={} port={} user={} password={} dbname={}".format(config.dbabbrev,
                                                                 host,
                                                                 port,
                                                                 config.dbusername,
                                                                 config.dbpass,
                                                                 config.dbname),
               shp,
               '-nln', shptablename]
        response = subprocess.call(cmd)

        uploadeddata = UserData(cuid, shptablename)
        db.session.add(uploadeddata)
        db.session.commit()

        return " ".join(cmd)
    #Cleanup
    #os.removedirs(tmpdir)

    return tmpdir

@mod_data.route('/cached/', methods=['GET'])
@login_required
def cached():
    return "CACHED"

@mod_data.route('/<uid>/<tablename>/')
@login_required
def get_dataset(uid, tablename):
    cuid = current_user.id
    if int(uid) != cuid:
        return "You are either not logged in or this is another user's data."
    else:
        response = {'status':'success','data':{}}
        if tablename in seen_classes:
            cls = current_app.class_references[tablename]
        else:
            db.metadata.reflect(bind=db.engine)
            seen_classes.add(tablename)
            cls = type(str(tablename), (GeoPoly, db.Model,), {'__tablename__':tablename,
                '__table_args__' : {'extend_existing': True}})
            current_app.class_references[tablename] = cls

        name = tablename.split('_')[1]
        response['data']['name'] = name
        response['data']['fields'] = [c.name for c in cls.__table__.columns]
        response['data']['fields'].append('geojson')
        #TODO: Add topojson support if the db is postgresql

        return jsonify(response)

@mod_data.route('/<uid>/<tablename>/<field>/')
@login_required
def get_dataset_field(uid, tablename, field):
    cuid = current_user.id
    if int(uid) != cuid:
        return "You are either not logged in or this is another user's data."
    else:
        response = {'status':'success','data':{}}
        if tablename in seen_classes:
            cls = current_app.class_references[tablename]
        else:
            db.metadata.reflect(bind=db.engine)
            seen_classes.add(tablename)
            cls = type(str(tablename), (GeoPoly, db.Model,), {'__tablename__':tablename,
                '__table_args__' : {'extend_existing': True}})
            current_app.class_references[tablename] = cls

        if field == config.geom_column:
            vector = cls.query.with_entities(geofuncs.ST_AsGeoJSON(getattr(cls, field))).all()
            response['data'][field] = [v[0] for v in vector]
        elif field == 'geojson':
            #TODO: How can this be cleaner?  Do I need 2 queries go get geojson?
            rows = cls.query.all()
            geoms = cls.query.with_entities(geofuncs.ST_AsGeoJSON(getattr(cls, config.geom_column))).all()
            features = []
            for i, row in enumerate(rows):
                attributes = row.as_dict()
                attributes.pop('wkb_geometry', None)
                current_feature = {'type':'Feature',
                        'geometry':ast.literal_eval(geoms[i][0]),
                        'properties':attributes}
                features.append(current_feature)
            geojson = {"type": "FeatureCollection","features": features}
            response['data']['geojson'] = geojson
        elif field == 'topojson':
            #TODO: Add topojson support if the DB is postgresql
            pass
        else:
            vector = cls.query.with_entities(getattr(cls, field)).all()
            response['data'][field] = [v[0] for v in vector]
        return jsonify(response)
