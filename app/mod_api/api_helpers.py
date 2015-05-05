import cPickle
import inspect
from urlparse import urlparse
import requests

from pmd import pmdwrapper

def getargorder(call):
    """
    Get the order of required args from a function.
    Does not support *args currently.
    """

    try:
        args = inspect.getargspec(call)
	try:
	    nargs = len(args.args)
	except:
	    nargs = 0
	try:
	    ndef = len(args.defaults)
	except:
 	    ndef = 0
	nreqargs = nargs - ndef
	argorder = args.args[:nreqargs]
    except:
        args = inspect.getargspec(call.__init__)
	try:
	    nargs = len(args.args)
	except:
	    nargs = 0
	try:
	    ndef = len(args.defaults)
	except:
	    ndef = 0
	nreqargs = nargs - ndef
	argorder = args.args[1:nreqargs] #Ignore self
    return argorder

def gettoken(a):
    url = False
    try:
	o = urlparse(a)

	if o.scheme in ['http', 'https', 'ftp']:
		url = True
    except:pass
    #If 'a' is a url, get the json data
    if url:
	if 'raw' in o.path.split('/'):
	    r = requests.get(a, verify=False)
            try:
		a = cPickle.loads(r.content)
		return a
	    except:
		print "ERROR: Can not load RAW data as a Python Object"
	else:
            r = requests.get(a, verify=False).json()
	    try:
                a = r['data']
	        return a
	    except: pass
    return False
