import cherrypy
from pysalrest import get_handlers, requesthandler

class PySALRest(object):
    def __init__(self, api):
        self._api = api
        self._handlers = get_handlers(api)

    def index(self):
        return "HTTP access to {} available at <a href='/api'>/api</a><br/> {}".format(self._api.__name__, self._api.__doc__)

    def api(self, resource, *pathargs, **kwargs):
        method = cherrypy.request.method.lower()
        response = requesthandler(self._handlers, method, resource, *pathargs, **kwargs)
        cherrypy.response.status = response.status
        prettyresponse = response.content.replace(',', '<br>')

        return prettyresponse

    index.exposed = True
    api.exposed = True


def start(api, host, port):
    CONF = {'global':{'server.socket_host':host,'server.socket_port':port}}

    ROOT = PySALRest(api)

    cherrypy.quickstart(ROOT, '/', CONF)


