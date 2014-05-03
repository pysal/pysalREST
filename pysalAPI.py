import pysalrest as pr

def get(ref=None, part=None):

    if ref is None:
        return pr.OkResponse([{k: getattr(rev, k) for k in dir(rev) if not k.startswith('_')}
            for rev in repo[0:'tip']])

def post(message=None):
    if message is None:
        return pr.MalformedResponse('Need to supply some arguments')
