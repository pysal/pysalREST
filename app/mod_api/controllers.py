from api_helpers import post, recursedict, get_docs, get_method

from flask import Blueprint, request, jsonify
from config import baseurl
from app import auth, db, libraryfunctions

mod_api = Blueprint('mod_api', __name__)

@mod_api.route('/', methods=['GET'])
@auth.login_required
def get_api():
    """
    The api homepage.
    """
    print "GETTING API"
    response = {'status':'success','links':[]}

    toplevel = libraryfunctions.keys()
    for i in toplevel:
        response['links'].append({'id':'{}'.format(i), 'href':baseurl + '/api/{}'.format( i)})
    return jsonify(response)

@mod_api.route('/<module>/', methods=['GET'])
@auth.login_required
def get_modules(module):
    """
    Modules within the
    """
    methods = libraryfunctions[module].keys()
    response = {'status':'success','links':[]}
    for i in methods:
        response['links'].append({'id':'{}'.format(i),
                                          'href':baseurl + '/api/{}/{}/'.format(module,i)})
    return jsonify(response)

@mod_api.route('/<module>/<method>/', methods=['GET', 'POST'])
@auth.login_required
def get_single_depth_method(module, method):
    if request.method == 'GET':
        if isinstance(libraryfunctions[module][method], dict):
            methods = libraryfunctions[module][method].keys()
            response = {'status':'success','links':[]}
            for i in methods:
                response['links'].append({'id':'{}'.format(i),
                                                'href':baseurl + '/api/{}/{}/{}'.format(module,method,i)})
            return jsonify(response)
        else:
            return jsonify(get_method(module, method))
    elif request.method == 'POST':
        if not request.json:
            response = {'status':'error','data':{}}
            response['data'] = 'Post datatype was not json'
            return jsonify(response), 400
        return jsonify(post(request, module, method))


@mod_api.route('/<module>/<module2>/<method>/', methods=['GET', 'POST'])
@auth.login_required
def get_nested_method(module, module2, method):
    if request.method == 'GET':
        return jsonify(get_method(module, method, module2=module2))
    else:
        if not request.json:
	    print "NOTJSON"
            response = {'status':'error','data':{}}
            response['data'] = 'Post datatype was not json'
            return jsonify(response), 400
        return jsonify(post(request, module, method, module2=module2))

@mod_api.route('/<module>/<method>/docs/', methods=['GET'])
@auth.login_required
def get_single_docs(module, method):
    return jsonify(get_docs(module, method))

@mod_api.route('/<module>/<module2>/<method>/docs/', methods=['GET'])
@auth.login_required
def get_nested_docs(module, module2, method):
    return jsonify(get_docs(module, method, module2=module2))
