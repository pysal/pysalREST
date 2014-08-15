import cherrypy
from flaskapp import app
from cherrypy import wsgiserver

def start(host, port):
    d = wsgiserver.WSGIPathInfoDispatcher({'/':app})
    server = wsgiserver.CherryPyWSGIServer((host, port),d)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

