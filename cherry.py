import time

import cherrypy
from app import app
import config
from paste.translogger import TransLogger

'''
def start(host, port):
    d = wsgiserver.WSGIPathInfoDispatcher({'/':app})
    server = wsgiserver.CherryPyWSGIServer((host, port),d)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
'''

def start():
    # Enable custom Paste access logging
    log_format = (
        '[%(time)s] REQUES %(REQUEST_METHOD)s %(status)s %(REQUEST_URI)s '
        '(%(REMOTE_ADDR)s) %(bytes)s'
    )
    
    app_logged = FotsTransLogger(app, format=log_format)
    cherrypy.tree.graft(app_logged, config.APPLICATION_ROOT)

    cherrypy.config.update({
	    'engine.autoreload_on':True,
	    'log.screen':True,
	    'server.socket_port':config.port,
	    'server.socket_host':config.host})
    cherrypy.engine.start()
    cherrypy.engine.block()

class FotsTransLogger(TransLogger):
    def write_log(self, environ, method, req_uri, start, status, bytes):
        """ We'll override the write_log function to remove the time offset so
        that the output aligns nicely with CherryPy's web server logging

        i.e.

        [08/Jan/2013:23:50:03] ENGINE Serving on 0.0.0.0:5000
        [08/Jan/2013:23:50:03] ENGINE Bus STARTED
        [08/Jan/2013:23:50:45 +1100] REQUES GET 200 / (192.168.172.1) 830

        becomes

        [08/Jan/2013:23:50:03] ENGINE Serving on 0.0.0.0:5000
        [08/Jan/2013:23:50:03] ENGINE Bus STARTED
        [08/Jan/2013:23:50:45] REQUES GET 200 / (192.168.172.1) 830
        """

        if bytes is None:
            bytes = '-'
        remote_addr = '-'
        if environ.get('HTTP_X_FORWARDED_FOR'):
            remote_addr = environ['HTTP_X_FORWARDED_FOR']
        elif environ.get('REMOTE_ADDR'):
            remote_addr = environ['REMOTE_ADDR']
        d = {
            'REMOTE_ADDR': remote_addr,
            'REMOTE_USER': environ.get('REMOTE_USER') or '-',
            'REQUEST_METHOD': method,
            'REQUEST_URI': req_uri,
            'HTTP_VERSION': environ.get('SERVER_PROTOCOL'),
            'time': time.strftime('%d/%b/%Y:%H:%M:%S', start),
            'status': status.split(None, 1)[0],
            'bytes': bytes,
            'HTTP_REFERER': environ.get('HTTP_REFERER', '-'),
            'HTTP_USER_AGENT': environ.get('HTTP_USER_AGENT', '-'),
        }
        message = self.format % d
        self.logger.log(self.logging_level, message)


