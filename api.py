import pysalrest as pr
import pysal as ps
import inspect

def get(ref=None, shapefile=None):

    method = ps.queen_from_shapefile
    print method, ref, shapefile
    if ref is None and shapefile is None:
        return pr.OkResponse('Need to supply a method call.  Currently on queen_from_shapefile is supported.')
    elif ref is not None and shapefile is None:
        args = inspect.getargspec(method)
        return pr.ErrorResponse("Arguments: {} Default Values: {}".format(args[0], args[1:]))
    else:
        #Data needs to be server side, i.e., in an upload directory
        shapefile = 'examples/' + shapefile
        w = method(shapefile)
        return pr.OkResponse(w.neighbors)


def post(message=None):
    if message is None:
        return pr.MalformedResponse('Need to supply some arguments')
