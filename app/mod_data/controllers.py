import ast
import decimal
import glob
import os
import subprocess
import tempfile

from flask import Blueprint, request, jsonify, g, current_app
from werkzeug.utils import secure_filename

import geoalchemy2.functions as geofuncs

from app import auth, db, seen_classes, cachedobjs
from app.mod_data.models import UserData, UserPyObj, GeoPoly, GEOMLOOKUP
from app.mod_data import upload_helpers as uph
import config

mod_data = Blueprint('mod_data', __name__)

@mod_data.route('/', methods=['GET'])
@auth.login_required
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
@auth.login_required
def listdata():
    """
    List the available datasets by querying the DB and
    returning metadata about the available user uploaded data.
    """
    cuid = g.user.id
    response = {'status':'success','data':{}}
    availabledata = UserData.query.filter_by(userid = cuid).all()
    for a in availabledata:
        dataname = a.datahash.split('_')
        entry = {'dataname':dataname[1],
                'href':'data/{}/{}'.format(cuid, a.datahash),
                'datecreated': a.date_created,
                'datemodified': a.date_modified}
        response['data'][a.id] = entry
    return jsonify(response)

@mod_data.route('/upload/', methods=['POST'])
@auth.login_required
def upload():
    """
    Upload to a temporary directory, validate, call ogr2ogr and write to the DB

    Using curl via the command line.
    ---------------------------------
    Example 1 is from pysal examples (from that dir)
    Example 2 is a subset of NAT, zipped.
    curl -X POST -F shp=@columbus.shp -F shx=@columbus.shx -F dbf=@columbus.dbf http://localhost:8080/data/upload/
    curl -X POST -F filename=@NAT_Subset.zip http://localhost:8080/data/upload/
    
    Do not forget to pass the login token (-u bigstring:unused)
    """
    print "UPLOADING"
    if hasattr(g.user, 'tmpdir'):    
        tmpdir = g.user.tmpdir
        print g.user
    else:
        tmpdir = tempfile.mkdtemp()
        g.user.tmpdir = tmpdir
    print tmpdir
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
               '-nlt', 'PROMOTE_TO_MULTI',
               '-nln', shptablename,
               '-lco', 'GEOMETRY_NAME={}'.format(config.geom_column)]

        response = subprocess.call(cmd)

        uploadeddata = UserData(cuid, shptablename)
        db.session.add(uploadeddata)
        db.session.commit()

        return " ".join(cmd)
    #Cleanup
    #os.removedirs(tmpdir)

    return tmpdir

@mod_data.route('/cached/', methods=['GET'])
@auth.login_required
def cached():
    """
    List the cached python objects for a given user.
    """
    cuid = g.user.id
    response = {'status':'success','data':{}}
    availabledata = UserPyObj.query.filter_by(userid = cuid).all()
    for a in availabledata:
        dataname = a.datahash.split('_')
        entry = {'dataname':dataname[1],
		'id':a.id,
                'href':'/data/cached/{}/{}'.format(cuid, a.datahash),
                'datecreated': a.date_created,
                'datemodified': a.date_modified}
        response['data'][a.id] = entry
    return jsonify(response)

@mod_data.route('/cached/<uid>/<objhash>', methods=['GET'])
@auth.login_required
def get_cached_entry(uid, objhash):
    cuid = g.user.id
    if int(uid) != cuid:
        return "You are either not logged in or this is another user's data."
    else:
        response = {'status':'success','data':{}}
        row = UserPyObj.query.filter_by(datahash = objhash).first()
        name = row.datahash.split('_')[1]
        response['data']['name'] = name
        response['data']['date_created'] = row.date_created
        response['data']['date_last_modified'] = row.date_modified

        row.get_pyobj()
        response['data']['methods'] = row.methods
        response['data']['attributes'] = row.attributes
        response['data']['provenance'] = {}
    return jsonify(response)

@mod_data.route('/cached/<uid>/<objhash>/<attribute>', methods=['GET'])
@auth.login_required
def get_cached_entry_attribute(uid, objhash, attribute):
    """
    Get an attribute from a PyObj via either the internal cache or a DB call.
    """
    cuid = g.user.id
    if int(uid) != cuid:
        return "You are either not logged in or this is another user's data."
    else:
        response = {'status':'success','data':{}}
        if not objhash in cachedobjs.keys():
            row = UserPyObj.query.filter_by(datahash = objhash).first()
            row.get_pyobj()
        else:
            pass
        try:
            response['data'][attribute] = getattr(row.liveobj, attribute)
            return jsonify(response)
        except:
            return jsonify({'status':'failure', 'data':'Unable to find attribute'})

@mod_data.route('/cached/<uid>/<objhash>/<method>', methods=['POST'])
@auth.login_required
def call_cached_centry_method(uid, objhash, method):
    raise NotImplementedError

@mod_data.route('/<uid>/<tablename>/')
@auth.login_required
def get_dataset(uid, tablename):
    cuid = g.user.id
    if int(uid) != cuid:
        return "You are either not logged in or this is another user's data."
    else:
        response = {'status':'success','data':{}}
        if tablename in seen_classes:
            cls = current_app.class_references[tablename]
        else:
            db.metadata.reflect(bind=db.engine)
            seen_classes.add(tablename)
            #Dynamic class creation using metaclasses
	    geomtype = "Polygon"
	    basegeomcls = GEOMLOOKUP[geomtype]
	    cls = type(str(tablename), (basegeomcls, db.Model,), {'__tablename__':tablename,
                '__table_args__' : {'extend_existing': True}})
            current_app.class_references[tablename] = cls

        name = tablename.split('_')[1]
        response['data']['name'] = name
        response['data']['fields'] = [c.name for c in cls.__table__.columns]
        response['data']['fields'].append('geojson')
        #TODO: Add topojson support if the db is postgresql

        return jsonify(response)

@mod_data.route('/<uid>/<tablename>/<field>/')
@auth.login_required
def get_dataset_field(uid, tablename, field):
    cuid = g.user.id
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
		for k, v in attributes.iteritems():
		    if isinstance(v, decimal.Decimal):
			attributes[k] = float(v)
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
    	    responsevector = [v[0] for v in vector]
	    if isinstance(responsevector[0], decimal.Decimal):
		for i, v in enumerate(responsevector):
 		    responsevector[i] = float(v)
            response['data'][field] = responsevector
        return jsonify(response)
