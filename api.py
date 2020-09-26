#!flask/bin/python
# pylint: disable-all
import sys, os
sys.path.append(os.getcwd()+'/worker')

from flask import Flask, jsonify, request, send_from_directory
from worker_controller import Main
from copy import deepcopy
from multidict import MultiDict

app = Flask(__name__)

HELP = '''
Ussage: api.py [OPTIONS]

--help          Show this message
--no-workers    Dont start any worker modules (Linux-only)
--bind [IP]     Start Flask API on this IP
--port [PORT]   Start Flask API on this PORT
        '''

def convertToDict(data):
    ''' Converts JSON to MultiDict '''
    md = MultiDict()
    for key in data:
        md.add(key, str(data[key]))
    return md

def removeEmpty(req):
    ''' Removes empty key->value pairs in req[data] '''
    for key in deepcopy(req['data']):
        if not req['data'][key]:
            req['data'].pop(key)
    return req

@app.route('/api/v0', methods=['GET'])
@app.route('/api/v0/', methods=['GET'])
def homepage():
    return jsonify({
        'success': True,
        'message1': 'Welcome to the mat-judge API v0',
        'message2': 'Please review our docs for more information',
        'message4': '~ Stevo Mitric (stevomitric2000@gmail.com)'
    })

@app.route('/api/v0/info')
def info():
    return jsonify({
        'token_access': bool(controller.db.getConf()[1]),
        'passive_submissions': bool(controller.db.getConf()[2]),
        'workers_active': controller.workers_connected(),
        'languages': controller.allowed_languages,
        'ip_status_timeout': controller.db.getConf()[3],
        'ip_submit_timeout': controller.db.getConf()[4],
    })

@app.route('/api/v0/status', methods=['GET'])
def status():
    # Limits check
    if not controller.limits.validateRequest('ip_status_timeout', request.remote_addr): return jsonify({'success': False, 'error': 'Request limit exceded'})
    req = { 
        'request': 'status',
        'data': {
            'submission_id': request.args.get('submission_id'),
            'output': request.args.get('output'),
        }
    }
    req = removeEmpty(req)

    # Token check
    token_validation = controller.token_manager.validateToken(request.args.get('token'), 4)
    if not token_validation[0]:
        return {'success': False, 'error': token_validation[1]}

    response = controller.add_queue(req)
    return jsonify(response)

@app.route('/api/v0/submit', methods=['POST'])
def submit():
    # Limits check
    if not controller.limits.validateRequest('ip_submit_timeout', request.remote_addr): return jsonify({'success': False, 'error': 'Request limit exceded'})
    if request.is_json: request.form = convertToDict(request.json)
    req = { 
        'request': 'submit',
        'data': {
            'code': request.form.get('code'),
            'language': request.form.get('language'),
            'time_limit': request.form.get('time_limit'),
            'memory_limit': request.form.get('memory_limit'),
            'testcases': request.form.get('testcases'),
            'testcases_id': request.form.get('testcases_id'),
            'grader': request.form.get('grader'),
        }
    }
    req = removeEmpty(req)

    # Token check
    token_validation = controller.token_manager.validateToken(request.form.get('token'), 3)
    if not token_validation[0]:
        return {'success': False, 'error': token_validation[1]}

    response = controller.add_queue(req)
    return jsonify(response)

@app.route('/api/v0/testcases', methods=['PUT'])
def testcases():
    if request.is_json: request.form = convertToDict(request.json)
    req = { 
        'request': 'testcases',
        'data': {
            'testcases': request.form.get('testcases'),
        }
    }
    req = removeEmpty(req)

    # Token check
    token_validation = controller.token_manager.validateToken(request.form.get('token'), 2)
    if not token_validation[0]:
        return {'success': False, 'error': token_validation[1]}

    response = controller.add_queue(req)
    return jsonify(response)

@app.route('/api/v0/token', methods=['POST'])
def createToken():
    if request.is_json: request.form = convertToDict(request.json)
    req = { 
        'request': 'create-token',
        'data': {
            'owner': request.form.get('owner'),
            'access_level': request.form.get('access_level'),
            'expiration': request.form.get('expiration'),
        }
    }
    req = removeEmpty(req)

    # Token check
    token_validation = controller.token_manager.validateToken(request.form.get('token'), 1)
    if not token_validation[0]:
        return {'success': False, 'error': token_validation[1]}

    response = controller.add_queue(req)
    return jsonify(response)

@app.route('/api/v0/token', methods=['GET'])
def infoToken():
    req = { 
        'request': 'info-token',
        'data': {
            'token': request.args.get('token'),
        }
    }

    response = controller.add_queue(req)
    return jsonify(response)
    
@app.route('/api/v0/token', methods=['DELETE'])
def deleteToken():
    if request.is_json: request.form = convertToDict(request.json)
    req = { 
        'request': 'delete-token',
        'data': {
            'token': request.form.get('token_delete'),
            'owner': request.form.get('owner'),
        }
    }

    # Token check
    token_validation = controller.token_manager.validateToken(request.form.get('token'), 1)
    if not token_validation[0]:
        return {'success': False, 'error': token_validation[1]}

    response = controller.add_queue(req)
    return jsonify(response)

@app.route('/api/v0/settings', methods=['POST'])
def settings():
    if request.is_json: request.form = convertToDict(request.json)
    req = {
        'request': 'settings',
        'data': {
            'token_access': request.form.get('token_access'),
            'passive_submissions': request.form.get('passive_submissions'),
            'ip_status_timeout': request.form.get('ip_status_timeout'),
            'ip_submit_timeout': request.form.get('ip_submit_timeout'),
        }
    }
    req = removeEmpty(req)

    # Token check
    token_validation = controller.token_manager.validateToken(request.form.get('token'), 1)
    if not token_validation[0]:
        return {'success': False, 'error': token_validation[1]}

    response = controller.add_queue(req)
    return jsonify(response)


@app.route('/', methods=['GET'])
@app.route('/testpage/', methods=['GET'])
@app.route('/testpage', methods=['GET'])
def testpage():
    return send_from_directory('', 'static/testpage.html')

if __name__ == '__main__':
    # Get all passed arguments
    args = {'--help':0, '--no-workers':0, '--bind': str, '--port':int}
    for arg in list(args):
        if arg in sys.argv:
            if args[arg] != 0:
                args[arg] = args[arg]( sys.argv[ sys.argv.index(arg)+1 ] )
        else:
            args.pop(arg)

    # Apply default values
    defaults = {'--bind': '0.0.0.0', '--port':5000}
    for default in defaults:
        if default not in args:
            args[default] = defaults[default]

    if '--help' in args:
        print(HELP)
    else: 
        controller = Main()
        controller.startLoop()

        app.run(debug=False, host = args['--bind'], port=args['--port'])

        controller.shutdown()