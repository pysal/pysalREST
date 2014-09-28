from api_helpers import post, recursedict, get_docs, get_method

from flask import Blueprint, request, jsonify
from app import db, pysalfunctions
from flask.ext.login import login_required

mod_api = Blueprint('mod_api', __name__)

@mod_api.route('/', methods=['GET'])
@login_required
def get_api():
    """
    The api homepage.
    """
    response = {'status':'success','data':{}}
    response['data']['links'] = []

    toplevel = pysalfunctions.keys()
    for i in toplevel:
        response['data']['links'].append({'id':'{}'.format(i), 'href':'/api/{}'.format( i)})
    return jsonify(response)

@mod_api.route('/<module>/', methods=['GET'])
@login_required
def get_modules(module):
    """
    Modules within the
    """
    methods = pysalfunctions[module].keys()
    response = {'status':'success','data':{}}
    response['data']['links'] = []
    for i in methods:
        response['data']['links'].append({'id':'{}'.format(i),
                                          'href':'/api/{}/{}/'.format(module,i)})
    return jsonify(response)

@mod_api.route('/<module>/<method>/', methods=['GET', 'POST'])
#@login_required
def get_single_depth_method(module, method):
    if request.method == 'GET':
        if isinstance(pysalfunctions[module][method], dict):
            methods = pysalfunctions[module][method].keys()
            response = {'status':'success','data':{}}
            response['data']['links'] = []
            for i in methods:
                response['data']['links'].append({'id':'{}'.format(i),
                                                'href':'/api/{}/{}/{}'.format(module,method,i)})
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
#@login_required
def get_nested_method(module, module2, method):
    if request.method == 'GET':
        return jsonify(get_method(module, method, module2=module2))
    else:
        if not request.json:
            response = {'status':'error','data':{}}
            response['data'] = 'Post datatype was not json'
            return jsonify(response), 400
        return jsonify(post(request, module, method, module2=module2))

@mod_api.route('/<module>/<method>/docs/', methods=['GET'])
@login_required
def get_single_docs(module, method):
    return jsonify(get_docs(module, method))

@mod_api.route('/<module>/<module2>/<method>/docs/', methods=['GET'])
@login_required
def get_nested_docs(module, module2, method):
    return jsonify(get_docs(module, method, module2=module2))
