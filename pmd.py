import inspect
import pysal as ps

def pmdwrapper(ps_obj):
    """
    Wrapping PySAL functions and classes to extend with meta_data for provenance

    Arguments
    ---------

    ps_obj: PySAL function or Class

    Returns
    -------
    Enhanced version of the original object. When this object is called, the return will be of the same type as the original object (function or class return) with an additional attribute:

    meta_data: dict
               meta_data['args']: list of arguments to the original object
               meta_data['kw_values']: values for the keyword arguments
               meta_data['positional_values']: values for the positional arguments
               meta_data['signature']: dict
               meta_data['signature']['kw_args']: dict with name of keyword args and default values
               meta_data['signature']['positional_args']: list of the name of positional arguments

    Examples
    --------
    >>> import pmd
    >>> import pysal as ps
    >>> qfs = pmd.wrapper(ps.queen_from_shapefile)
    >>> columbus=ps.examples.get_path('columbus.shp')
    >>> w = qfs(columbus)
    >>> w.meta_data
    {'positional_values': ('/Users/serge/Documents/p/pysal/src/pysal/pysal/examples/columbus.shp',), 'args': ['shapefile', 'idVariable', 'sparse'], 'kw_values': {}, 'signature': {'kw_args': {'idVariable': None, 'sparse': False}, 'positional_args': ['shapefile']}}
    >>> w1 = qfs(columbus, idVariable='POLYID')
    >>> w1.meta_data
    {'positional_values': ('/Users/serge/Documents/p/pysal/src/pysal/pysal/examples/columbus.shp',), 'args': ['shapefile', 'idVariable', 'sparse'], 'kw_values': {'idVariable': 'POLYID'}, 'signature': {'kw_args': {'idVariable': None, 'sparse': False}, 'positional_args': ['shapefile']}}
    >>> neighbors = ps.lat2W().neighbors
    >>> W = pmd.wrapper(ps.W)
    >>> w2 = W(neighbors)
    >>> w2.meta_data
    {'positional_values': ({0: [5, 1], 1: [0, 6, 2], 2: [1, 7, 3], 3: [2, 8, 4], 4: [3, 9], 5: [0, 10, 6], 6: [1, 5, 11, 7], 7: [2, 6, 12, 8], 8: [3, 7, 13, 9], 9: [4, 8, 14], 10: [5, 15, 11], 11: [6, 10, 16, 12], 12: [7, 11, 17, 13], 13: [8, 12, 18, 14], 14: [9, 13, 19], 15: [10, 20, 16], 16: [11, 15, 21, 17], 17: [12, 16, 22, 18], 18: [13, 17, 23, 19], 19: [14, 18, 24], 20: [15, 21], 21: [16, 20, 22], 22: [17, 21, 23], 23: [18, 22, 24], 24: [19, 23]},), 'args': ['self', 'neighbors', 'weights', 'id_order', 'silent_island_warning', 'ids'], 'kw_values': {}, 'signature': {'kw_args': {'silent_island_warning': False, 'id_order': None, 'weights': None, 'ids': None}, 'positional_args': ['self', 'neighbors']}}

    """
    def inner(*args, **kwargs):
        # call the pysal object
        ret = ps_obj(*args, **kwargs)
        # build up meta_data
        meta_data = {}
        meta_data['positional_values'] = args[:]
        meta_data['kw_values'] = kwargs
        if inspect.isclass(ps_obj):
            args = inspect.getargspec(ps_obj.__init__)
        else:
            args = inspect.getargspec(ps_obj)

        # parse the signature of the pysal object
        n_kw = 0
        if args.defaults:
            n_kw = len(args.defaults)
        n_args = len(args.args)
        signature = {}
        if n_args == n_kw:
            signature['positional_args'] = None
            if n_kw == 1:
                kw_args = {args.args: args.defaults}
                signature['kw_args'] = kw_args
            else:
                signature['kw_args'] = dict(zip(args.args, args.defaults))
        else:
            n_positional = n_args - n_kw
            signature['positional_args'] = args.args[:n_positional]
            if n_kw > 0:
                signature['kw_args'] = dict(zip(args.args[n_positional:], args.defaults))
        meta_data['args'] = args.args
        meta_data['signature'] = signature
        ret.meta_data = meta_data
        return ret
    return inner
