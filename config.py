DEBUG=True
THREADS_PER_PAGE = 2
CSRF_ENABLED = True
SECRET_KEY = '\x97}\x81k\x94Hs\xc9R\\L\x9f\xf3J\x9e\x85nn\xca\xa5_\xc8\xacg'
CSRF_SESSION_KEY = "makeme"

#Define the application directory
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

#API
api = 'pysalrest'

#SERVER
server = 'cherry'
port = 8081
host = '0.0.0.0'

#Database
db = '10.0.0.0'
dbname = 'pysal'
dbpass = 'TEST'

#Logging
loglocation = 'logging.log'


