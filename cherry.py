import cherrypy
from flaskapp import app
from cherrypy import wsgiserver

'''
from flask import Flask, render_template
import jinja2 as j2
from pysalrest import get_handlers, requesthandler, funcs, methods

#I dislike the coupling here with the api imports, but
# this is a single library



class PySALRest(object):
    def __init__(self, api):
        self._api = api
        self._handlers = get_handlers(api)
        #templateloader = j2.FileSystemLoader(searchpath='templates/')
        #self.templateenv = j2.Environment(loader=templateloader)

    @cherrypy.expose
    def index(self):
        #template = self.templateenv.get_template('index.tmp')

        templatevars = {'funcs':funcs}
        return render_template('index.tmp')
        #return "HTTP access to {} available at <a href='/pysal/api'>/pysal/api</a><br/> {}".format(self._api.__name__, self._api.__doc__)

    @cherrypy.expose
    def pysal(self, resource, *pathargs, **kwargs):
        try:
            method = cherrypy.request.method.lower()
            response = requesthandler(self._handlers, method, resource, *pathargs, **kwargs)
            cherrypy.response.status = response.status



            #prettyresponse = response.content.replace(',', '<br>')
            return response
        except:
            return "HTTP access to {} available at <a href='/pysal/api'>/pysal/api</a><br/> {}".format(self._api.__name__, self._api.__doc__)
'''
def start(host, port):
    d = wsgiserver.WSGIPathInfoDispatcher({'/':app})
    server = wsgiserver.CherryPyWSGIServer((host, port),d)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

    #CONF = {'global':{'server.socket_host':host,'server.socket_port':port}}
    #ROOT = PySALRest(api)

    #cherrypy.quickstart(ROOT, '/', CONF)


