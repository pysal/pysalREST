import cherrypy
import jinja2
from pysalrest import get_handlers, requesthandler

class PySALRest(object):
    def __init__(self, api):
        self._api = api
        self._handlers = get_handlers(api)

    @cherrypy.expose
    def index(self):
        return "HTTP access to {} available at <a href='/pysal/api'>/pysal/api</a><br/> {}".format(self._api.__name__, self._api.__doc__)

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

    @cherrypy.expose
    def pysaldocos(self):
        return "DOCOS links"

def start(api, host, port):
    CONF = {'global':{'server.socket_host':host,'server.socket_port':port}}
    ROOT = PySALRest(api)

    cherrypy.quickstart(ROOT, '/', CONF)


