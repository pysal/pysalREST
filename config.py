###GENERAL###
DEBUG=True
THREADS_PER_PAGE = 2
#CSRF_ENABLED = False
SECRET_KEY = ''
#CSRF_SESSION_KEY = "makeme"
SESSION_COOKIE_NAME = 'session'

ALLOWED_EXTENSIONS = set(['shp', 'dbf', 'shx', 'prj', 'zip', 'amd', 'pmd'])

#Define the application directory
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

###API###
library = 'pysal'
api = 'pysalrest'
loadmap = 'libraryconfig.json'

###SERVER###
server = 'cherry'
port = 8080
host = '10.0.21.105'

"""
Base URL is the URL of the API.
Base data URL can be the same url, if pysalREST is to be run as a
 single server service.  Alternatively, you can specify a URL, if
 pysalDATA is to be used to run a distinct data service.
"""
APPLICATION_ROOT = '/'
baseurl = 'https://webpool.csf.asu.edu/' + api
basedataurl = 'https://webpool.csf.asu.edu/pysaldata'

###Database setup###
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
dbhost = ''
dbusername = ''
dbpass = ''
dbname = ''
SQLALCHEMY_DATABASE_URI = '{}{}:{}@{}/{}'.format(dbtype,
                                                 dbusername,
                                                 dbpass,
                                                 dbhost,
                                                 dbname)
geom_column = 'wkb_geometry'

###3rd Party###
ogr2ogr = '/home/apache/anaconda/bin/ogr2ogr' #'/usr/bin/ogr2ogr'

###Logs###
loglocation = 'logging.log'

###OAuth Providers - The admin must be registered with each###
OAUTH_CREDENTIALS = {
    'twitter': {
        'id': 'S5XPbiSLIb1nB1L8zYRU2xiHc',
        'secret': ''
    },
    'github': {
        'id':'da690d5f5913c04e4f6b',
	'secret':''
    }
}
