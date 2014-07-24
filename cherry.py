import cherrypy
from flaskapp import app, setdb
from cherrypy import wsgiserver

def start(host, port, db):
    d = wsgiserver.WSGIPathInfoDispatcher({'/':app})
    server = wsgiserver.CherryPyWSGIServer((host, port),d)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

