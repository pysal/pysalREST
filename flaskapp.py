from flask import Flask, render_template, jsonify
from flask.ext.restful import Api, Resource

from api import funcs

app = Flask(__name__)
api = Api(app)

standardsuccess = {'status':'success','data':{}}
standarderror = {'status':'error','data':{}}
standardfail = {'status':'fail','data':{}}


@app.route('/', methods=['GET'])
def home():
    return 'You are home'

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

@app.route('/api/region', methods=['GET'])
def region():
    methods = funcs['region'].keys()
    response = standardsuccess
    response['data']['methods'] = []
    for i in methods:
        response['data']['methods'].append({i:'/api/region/{}'.format(i)})
    return jsonify(response)

@app.route('/api/region/<method>', methods=['GET', 'POST'])
def regionalization(method):
    return str(method)

api.add_resource(UserAPI, '/api', endpoint='api')

if __name__ == '__main__':
    app.config.update(DEBUG=True)
    app.run()
