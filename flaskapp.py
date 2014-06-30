import inspect

from flask import Flask, render_template, jsonify, request
from flask.ext.restful import Api, Resource

from api import funcs

app = Flask(__name__)
api = Api(app)

standardsuccess = {'status':'success','data':{}}
standarderror = {'status':'error','data':{}}
standardfail = {'status':'fail','data':{}}


@app.route('/', methods=['GET'])
def home():
    response = {'status':'success','data':{}}
    response['data']['href'] = {'api':'/api'}
    return jsonify(response)

#Can this be autoamted or does it need to happen for each module?
#Alternatively, can I use the resource syntax, below, with a class factory?
@app.route('/api/<module>', methods=['GET'])
def list_region(module):
    methods = funcs[module].keys()
    response = {'status':'success','data':{}}
    response['data']['methods'] = []
    for i in methods:
        response['data']['methods'].append({i:'/api/{}/{}'.format(module,i)})
    return jsonify(response)

@app.route('/api/<module>/<method>', methods=['GET'])
def get_region(module, method):
    """
    Query the API to get the docstring and the parameters.
    """
    print funcs[module][method]
    #Setup the response strings
    response = {'status':'success','data':{}}
    response['data']['docstring'] = []
    response['data']['template'] = {}

    #Extract the method from the method dict
    method = funcs[module][method]

    docs = inspect.getdoc(method)
    print docs
    for l in docs.split('\n'):
        response['data']['docstring'].append(l)

    #Generate the post template
    try:
        reqargs = inspect.getargspec(method)
    except:
        reqargs = inspect.getargspec(method.__init__)
        args = reqargs.args
        args.remove('self')
        print args
        print reqargs.defaults
        #reqargs.remove('self')
    print reqargs
    #Update the post template - this documents how a post should look
    response['data']['template'] = {}
    for a in reqargs:
        for line in docs.split('\n'):
            if ' {} '.format(a) in line and ':' in line:
                inputtype = line.split(':')[-1]
        response['data']['template'].update({a:inputtype})

    return jsonify(response)

@app.route('/api/<module>/<method>', methods=['POST'])
def post_region(module,method):
    if not request.json:
        response = {'status':'error','data':{}}
        standarderror['data'] = 'Post datatype was not json'
        return jsonify(standarderror), 400
    else:
        response = {'status':'success','data':{}}
        response['data'] = request.json



        return jsonify(response)


class UserAPI(Resource):
    def get(self):
        try:
            toplevel = funcs.keys()
            response = standardsuccess
            response['data']['modules'] = []
            for i in toplevel:
                response['data']['modules'].append({i:'/api/{}'.format(i)})
            return jsonify(response)
        except:
            response = standarderror
            response['data'] = 'Unable to load module list'
            return jsonify(response)
api.add_resource(UserAPI, '/api', endpoint='api')

if __name__ == '__main__':
    app.config.update(DEBUG=True)
    app.run()
