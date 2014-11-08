import cPickle
import inspect

from app import db
from geoalchemy2 import Geometry

#Base DB Model - All other tables subclass this class
class Base(db.Model):

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())

#User to Data Lookup Table
class UserData(Base):

    __tablename__ = 'userdata'

    userid = db.Column(db.Integer, nullable=False)
    datahash = db.Column(db.String(256), nullable=False)

    def __init__(self, userid, datahash):
        self.userid = userid
        self.datahash = datahash

    def __repr__(self):
        return '<User: {} | Data: {}>'.format(self.userid,
                                              self.datahash)

class UserPyObj(Base):

    __tablename__ = 'userpyobj'

    userid = db.Column(db.Integer, nullable=False)
    pyobj = db.Column(db.LargeBinary, nullable=False)
    datahash = db.Column(db.String(256), nullable=False)

    def __init__(self, userid, pyobj, datahash=None):
        self.userid = userid
        self.pyobj = pyobj
        self.datahash = datahash

    def get_pyobj(self):
        """
        Return a python object, loaded via cPickle, from the DB and parse
        out the methods and attributes.
        """
        self.liveobj = cPickle.loads(str(self.pyobj))
        self.methods = {}
        methods = inspect.getmembers(self.liveobj, predicate=inspect.ismethod)
        for m in methods:
            if m[0][0] != '_':
                self.methods[m[0]] = inspect.getargspec(m[1])
        #Parse the available attributes
        self.attributes = []
        attrs = inspect.getmembers(self.liveobj,lambda i : not(inspect.ismethod(i)))
        for a in attrs:
            if not a[0].startswith('__'):
                self.attributes.append(a[0])

    def __repr__(self):
        return '<User: {} has a pyobj names {}.>'.format(self.userid, self.datahash)

class GeoPoly():
    wkb_geometry = db.Column(Geometry("POLYGON"))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class GeoMultiPoly():
    wkb_geometry = db.Column(Geometry("MULTIPOLYGON"))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

GEOMLOOKUP = {'Polygon':GeoPoly,
	     'MultiPolygon':GeoMultiPoly}
