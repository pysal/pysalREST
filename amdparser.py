import ast
import json
import os
import sys
from urlparse import urlparse
import urllib

import numpy as np
import pysal as ps


def parsewmd(jwmd, uploaddir=None):

    #Get the URI
    uri = jwmd['input1']['data1']['uri']
    url = urlparse(uri)

    if url.scheme == 'http':
        basename = url.path.split('/')[-1]

        if uploaddir != None:
            basename = os.path.join(uploaddir, basename)

        #The WMD never spcifies the .shx, but PySAL needs it
        shx = basename.replace('.shp', '.shx')
        shxuri = uri.replace('.shp', '.shx')

        #Download both files locally
        response = urllib.urlretrieve(uri, basename)
        response = urllib.urlretrieve(shxuri, shx)

    elif url.scheme == 'file':
        pass

    #Get the generation information
    wtype = jwmd['weight_type']
    transform = jwmd['transform']


    #Populate the W
    if wtype.lower() == 'rook':
        w = ps.rook_from_shapefile(basename)
    elif wtype.lower() == 'queen':
        w = ps.queen_from_shapefile(basename)

    #Transform
    w.transform = transform

    return w

def gety(attribute, uploaddir=None):
    uri = attribute['uri']
    name = attribute['name']
    url = urlparse(uri)

    if url.scheme == 'http':
        basename = url.path.split('/')[-1]
        if basename != None:
            basename = os.path.join(uploaddir, basename)
        response = urllib.urlretrieve(uri, basename)

    elif url.scheme == 'file':
        basename = url.path
        pass

    db = ps.open(basename, 'r')
    y = np.array(db.by_col(name))
    return y

def generateW(uri, wtype, uploaddir=None):
    #First get the file
    url = urlparse(uri)
    if url.scheme == 'http':
        basename = url.path.split('/')[-1]
        if uploaddir != None:
            basename = os.path.join(uploaddir, basename)
        response = urllib.urlretrieve(uri, basename)
    elif url.scheme == 'file':
        pass

    #Then parse the file type
    if wtype == 'prov':
        with open(basename) as jdata:
            jwmd = json.load(jdata)
            w = parsewmd(jwmd, uploaddir)
    elif wtype == 'gal':
        w = ps.open(basename).read()


    return w

def parse_analysis(funcs, method):
    #Sloppy search
    method = method['method']
    #Terrible hack
    if method == 'getis':
        method = 'G'

    call = None
    for k, v in funcs.iteritems():
        if call != None:
            break
        if isinstance(v, dict):
            for nk, nv in v.iteritems():
                if isinstance(nv, dict):
                    for nnk, nnv in nv.iteritems():
                        if nnk == method:
                            callpath = [k, nk, nnk]
                            call = nnv

                            break
                elif nk == method:
                    callpath = [k, nk]
                    call = nv
                    break
        else:
            if k == method:
                callpath = [k]
                call = v
                break
    return callpath, call

def main(metadata):

    funcs = {}

    with open(metadata) as jdata:
        amd = json.load(jdata)

    #Gather the inputs or confirm they exist
    wspecs = amd['input']['weights']
    wobj = generateW(wspecs['uri'], wspecs['type'])

    #Can easily be an iterator for multiple attributes.
    #Here order might be an issue
    attribute = amd['input']['attribute']
    y = gety(attribute)

    #Map the analysis to a pysal function

    #Extract the parameters
    kwargs = amd['parameters']

    #How do we know the mapping of the order of the input args?
    #Moran and getis as reversed if we use the order of the JSON
    args = [y, w]

    call = parse_analysis(funcs, amd['analysis_type'])

if __name__ == '__main__':
    main(sys.argv[1])
