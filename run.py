import argparse
import importlib
import inspect
import types

from app import app

def _parse_args():
    """
    Parse the command line arguments - these override the config file.close(

    This is useful if you want to default to cherrypy, but fire a flask dev.
    server manually once in a while.
    """
    parser = argparse.ArgumentParser(description='Serve your API RESTful(-ish?)')
    parser.add_argument('--cfg', help='Config file (pyrest.cfg)', required=False)
    parser.add_argument('--server', help='App server to use (cherry or flask)', required=False)
    parser.add_argument('--host', help='Address to bind to (0.0.0.0)', required=False)
    parser.add_argument('--port', type=int, help='Port to listen on (8080)', required=False)
    #TODO: Add arguments for database path, username, login creds.
    return vars(parser.parse_args())

def _get_config():
    #Here we set defaults - they are first overwritten via the config file,
    # then via commandline args
    args = {'server': 'cherry',
            'cfg': 'config',
            'port': 8080,
            'host': '0.0.0.0'
            }
    args.update({k:v for (k,v) in _parse_args().items() if v is not None})
    configfile = args['cfg']
    configmodule = importlib.import_module(args['cfg'])
    keys = [v for v in dir(configmodule) if (not v.startswith('__'))]
    configdict = {}
    for k in keys:
        val = configmodule.__dict__[k]
        if not isinstance(val, types.ModuleType):
            configdict[k] = val
    configdict.update(args)
    print configdict
    return configdict

def main():
    config = _get_config()

    if config['server'] == 'cherry':
        #Run the stable, cherrypy server
        from cherrypy import wsgiserver
        d = wsgiserver.WSGIPathInfoDispatcher({'/':app})
        server = wsgiserver.CherryPyWSGIServer((config['host'], config['port']),d)
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()
    else:
        #Run the development server
        app.run(host=config['host'], port=config['port'], debug=config['DEBUG'])

if __name__ =='__main__':
    main()
