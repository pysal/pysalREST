import pysalrest as pr
import pysal as ps


def get(ref=None, part=None):
    method = ps.queen_from_shapefile
    print method, ref, part
    if ref is None:
        return pr.OkResponse([{k: getattr(rev, k) for k in dir(rev) if not k.startswith('_')} for rev in repo[0:'tip']])


def post(message=None):
    print "POST"
    if message is None:
        return pr.MalformedResponse('Need to supply some arguments')
