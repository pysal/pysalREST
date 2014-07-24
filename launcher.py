import pysalrest
import argparse
import ConfigParser
import os.path
import importlib
from flaskapp import setdb

def _parse_args():
    parser = argparse.ArgumentParser(description='Serve your API RESTful(-ish?)')
    parser.add_argument('--cfg', help='Config file (pyrest.cfg)', required=False)
    parser.add_argument('--server', help='App server to use (cherrypy)', required=False)
    parser.add_argument('--host', help='Address to bind to (0.0.0.0)', required=False)
    parser.add_argument('--port', type=int, help='Port to listen on (8080)', required=False)
    parser.add_argument('--api', help='Package to serve (None)')
    parser.add_argument('--db', help='Shelve filename')
    return vars(parser.parse_args())

def _parse_file(path):
    if not os.path.exists(path):
        return {}
    config = ConfigParser.ConfigParser()
    config.read(path)
    return dict(config['pyrest'])

def _get_config():
    args = {'server': 'cherrypy',
            'cfg': 'pysalrest.cfg',
            'api': 'pysalrest',
            'port': 8080,
            'host': '0.0.0.0',
            'db':'objstorage.db'
            }
    args.update({k:v for (k,v) in _parse_args().items() if v is not None})
    configfile = args['cfg']
    cfgopts = _parse_file(configfile)
    cfgopts.update(args)
    return cfgopts

def main():
    cfg = _get_config()
    try:
        engine = importlib.import_module(cfg['server'])
        print engine
    except ImportError:
        raise ImportError("Could not load server integration implementation: %s" % (cfg['server'],))
    try:
        api = importlib.import_module(cfg['api'])
        print "Launching the API contained at: ", api
    except ImportError:
        raise ImportError("Could not load API: %s" % (cfg['api'],))

    engine.start(cfg['host'], cfg['port'], cfg['db'])

if __name__ == '__main__':
    main()
