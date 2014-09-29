DEBUG=True
THREADS_PER_PAGE = 2
CSRF_ENABLED = True
SECRET_KEY = '\x97}\x81k\x94Hs\xc9R\\L\x9f\xf3J\x9e\x85nn\xca\xa5_\xc8\xacg'
CSRF_SESSION_KEY = "makeme"

ALLOWED_EXTENSIONS = set(['shp', 'dbf', 'shx', 'prj', 'zip', 'amd', 'pmd'])

#Define the application directory
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

#API
api = 'pysalrest'

#SERVER
server = 'cherry'
port = 8080
host = '0.0.0.0'

#Database
"""
For a local SQLite DB:
dbtypename = 'Sqlite'
dbabbrev = '??'
dbtype = 'sqlite:///'
dbhost = os.path.join(BASE_DIR, 'pysalrest.db')
dbusername = ''
dbpass = ''
dbname = ''
"""

dbtypename = 'PostgreSQL'  #Used by ogr2ogr, must be a valid ogr2ogr db
dbabbrev = 'PG'
dbtype = 'postgresql+psycopg2://'
dbhost = 'localhost:5432'
dbusername = 'postgres'
dbpass = 'postgres'
dbname = 'pysalrest'
SQLALCHEMY_DATABASE_URI = '{}{}:{}@{}/{}'.format(dbtype,
                                                 dbusername,
                                                 dbpass,
                                                 dbhost,
                                                 dbname)
geom_column = 'wkb_geometry'

#GDAL Commands
ogr2ogr = '/Users/jay/anaconda/bin/ogr2ogr' #'/usr/bin/ogr2ogr'

#Logging
loglocation = 'logging.log'
