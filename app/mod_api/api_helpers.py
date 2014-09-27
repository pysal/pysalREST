import ast
import inspect

import numpy as np
import pysal as ps

from pmd import pmdwrapper
from app import pysalfunctions


def post(request, module,method, module2=None):
    """
    To make a POST using CURL:
    Fisher-Jenks using the Hartigan Olympic time example
    curl -i -H "Content-Type: application/json" -X POST -d '{"args":["[12, 10.8, 11, 10.8, 10.8, 10.6, 10.8, 10.3, 10.3,10.3,10.4,10.5,10.2,10.0,9.9]"], "kwargs":{"k":5}}' http://localhost:8080/api/esda/mapclassify/Fisher_Jenks/

    or

    Using the CherryPy server on port 8080
    Queen from shapefile - NOTE: The file must be uploaded already
    curl -i -H "Content-Type: application/json" -X POST -d '{"args":[NAT.shp]}' http://localhost:8080/api/weights/queen_from_shapefile/
    """
    #TODO: This needs a refactor badly - handling python objs, etc.
    if not request.json:
        response = {'status':'error','data':{}}
        response['data'] = 'Post datatype was not json'
        return jsonify(response), 400
    else:
        response = {'status':'success','data':{}}
        #Setup the call, the args and the kwargs
        if module2 == None:
            call = pmdwrapper(pysalfunctions[module][method])
        else:
            call = pmdwrapper(pysalfunctions[module][module2][method])

        #Parse the args
        keys = request.json.keys()
        req = request.json

        #Setup the python arg / kwarg containers
        args = []
        kwargs = {}
        if 'args' in keys:
            for a in req['args']:
                try:
                    args.append(ast.literal_eval(a))
                except:
                    args.append(a)
        if 'kwargs' in keys:
            for k, v in req['kwargs'].iteritems():
                try:
                    kwargs[k] =  ast.literal_eval(v)
                except:
                    kwargs[k] = v
        # or if they are uploaded shapefiles
        for i, a in enumerate(args):
            try:
                if a in UPLOADED_FILES:
                    args[i] = UPLOAD_FOLDER + '/' +  a
                    shpname = a.split('.')[0]
            except: pass
            try:
                if a.split('_')[0] == 'cached':
                    cacheid = a.split('_')[1]
                    query = "SELECT Obj FROM WObj WHERE ID = {}".format(cacheid)
                    cur = get_db().cursor().execute(query)
                    result = cur.fetchone()[0]
                    obj = cPickle.loads(str(result))

                    args[i] = obj
                    cur.close()
            except: pass

        for k, v in kwargs.iteritems():
            try:
                if v in UPLOADED_FILES:
                    kwargs[k] = os.path.join(UPLOAD_FOLDER, v)
            except: pass

            try:
                if v.split('_')[0] == 'cached':
                    cacheid = v.split('_')[1]
                    query = "SELECT Obj FROM WObj WHERE ID = {}".format(cacheid)
                    cur = get_db().cursor().execute(query)
                    result = cur.fetchone()[0]
                    obj = cPickle.loads(str(result))

                    kwargs[k] = obj
                    cur.close()
            except: pass


        #This is a hack until I get the vector/list checking going on
        if module == 'esda':
            args[0] = np.array(args[0])

        #Make the call and get the return items
        funcreturn = call(*args, **kwargs)

        #Write the W Object to the database
        if isinstance(funcreturn, ps.W):
            pdata = cPickle.dumps(funcreturn, cPickle.HIGHEST_PROTOCOL)
            cur = get_db().cursor()
            if method == 'queen_from_shapefile':
                m = 'Queen'
            else:
                m = 'Rook'
            indb = False

            #Query the db to see if the name / type is in the db
            query = "SELECT Type, Shapefile FROM WObj"
            cur = get_db().cursor().execute(query)
            result = cur.fetchall()
            for r in result:
                if r[0] == m and r[1] == shpname:
                    indb = True
                    break

            if indb == False:
                obj = (m, sqlite3.Binary(pdata), funcreturn._shpName)
                cur.execute("INSERT INTO WObj values (NULL, ?, ?, ?)",obj)
                get_db().commit()
            cur.close()

            response['data'] = {'Shapefile':funcreturn._shpName,
                                'Weight Type':method}
        else:
            funcreturn = recursedict(vars(funcreturn))
            response['data'] = funcreturn

        return response


def recursedict(inputdict):
    #TODO: Make recursive - once I understand the PMD structure
    for k, v in inputdict.iteritems():
        if k == 'meta_data':
            newpositionalvalues = []
            oldpositionalvalues = v['positional_values']

            for i in oldpositionalvalues:
                if isinstance(i, np.ndarray):
                    newpositionalvalues.append(i.tolist())
                elif isinstance(i, ps.W):
                    newpositionalvalues.append(i.__repr__())
                else:
                    newpositionalvalues.append(i)

            v['positional_values'] = newpositionalvalues

        elif isinstance(v, np.ndarray):
            inputdict[k] = v.tolist()
        elif isinstance(v, ps.W):
            inputdict[k] = v.__repr__()

    return inputdict


def get_docs(module, method, module2=None):
    """
    Query the API to get the doc string of the method
    """
    response = {'status':'success','data':{}}
    response['data']['docstring'] = []

    #Extract the method from the method dict
    if module2 == None:
        method = pysalfunctions[module][method]
    else:
        method = pysalfunctions[module][module2][method]

    #Introspect the docs
    docs = inspect.getdoc(method)
    for l in docs.split('\n'):
        response['data']['docstring'].append(l)
    return response

def get_method(module, method, module2 = None):
    """
    Query the API to get the POST parameters.
    """
    #Setup the response strings
    response = {'status':'success','data':{}}
    response['data']['post_template'] = {}
    mname = method
    #Extract the method from the method dict
    if module2 == None:
        method = pysalfunctions[module][method]
    else:
        method = pysalfunctions[module][module2][method]

    #Inspect the method to get the arguments
    try:
        reqargs = inspect.getargspec(method)
    except:
        reqargs = inspect.getargspec(method.__init__)

    args = reqargs.args
    defaults = list(reqargs.defaults)
    try:
        args.remove('self')
    except:
        pass

    #Pack the arguments into the pos_template
    response['data']['post_template'] = {'args':[], 'kwargs':{}}
    diff = len(defaults) - len(args)
    for i, arg in enumerate(args):
        if diff < 0:
            diff += 1
            response['data']['post_template']['args'].append(arg)
        else:
            response['data']['post_template']['kwargs'][arg] = defaults[diff]

    response['data']['links'] = {'id':'docs',
                                 'href':'{}/{}/docs/'.format(module, mname)}
    return response

