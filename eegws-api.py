from flask import Flask, Response, jsonify, request, abort, make_response
from flask.ext.httpauth import HTTPBasicAuth
from bson import json_util
from pymongo import MongoClient

auth = HTTPBasicAuth()

client = MongoClient()
db = client.testeegdb
recordings_collection = db.recordings
users_collection = db.users

app = Flask(__name__)


rec = {
        'timestamp': [1428262635, 1428262636, 1428262637, 1428262638, 1428262639],
        'device': 'emotiv',
        'frequency': 128,
        'electrodes': {'AF3': [10, 20, 33, 12, 56],
                       'O1': [12, 57, 88, 32, 15],
                       'P7': [22, 47, 78, 62, 35]},
        'quality': {'AF3': [100, 90, 90, 90, 90],
                    'O1': [92, 76, 88, 78, 90],
                    'P7': [100, 90, 93, 90, 90]},
        'gyroscope': {'gyroX': [-100, 0, 150, 190, 200], 'gyroY': [-150, -90, 0, 80, 120]},
        'auxdata': {'battery': 100},
        'annotation': 'Blinking experiment 05-04-2015',
        'userid': 'd8f9419e-dbc2-11e4-b9d6-1681e6b88ec1',
        'good': True
        }

user = {
        'userid': 'd8f9419e-dbc2-11e4-b9d6-1681e6b88ec1',
        'username': 'al1na',
        'password': 'python',
        'birthyear': 1900,
        'gender': 'F',
        'organization': 'DTU',
        'public': True
        }

#recordings_collection.insert(rec)
#users_collection.insert(user)


@auth.get_password
def get_password(username):
    user = users_collection.find({"username": username}, {"password": 1, "_id": 0})
    if user.count() == 0:
        abort(404)
    for u in user:
        password = u.get('password')
    return password


@app.route('/mobileeg/api/v1/recordings', methods=['GET'])
@auth.login_required
def get_recordings():
    #TODO: to provide only the public recordings (check if public=True for the user)
    recordings_list = []
    for recording in recordings_collection.find():
        recording.pop('_id')
        recordings_list.append(recording)
    return jsonify({'recordings':recordings_list})
    #return Response(json_util.dumps({'page' : recordings_list}), mimetype='application/json')


@app.route('/mobileeg/api/v1/recordings', methods=['POST'])
@auth.login_required
def create_recording():
    global userid
    if not request.json:
        abort(400)
    user = users_collection.find({"username": auth.username()})
    for u in user:
        userid = u.get('userid')
    rec = {
            'timestamp': request.json['timestamp'],
            'device': request.json['device'],
            'frequency': request.json['frequency'],
            'electrodes': request.json['electrodes'],
            'quality': request.json['quality'],
            'gyroscope': request.json['gyroscope'],
            'auxdata': request.json['auxdata'],
            'annotation': request.json['annotation'],
            'good': True,
            'userid': userid
            }
    recordings_collection.insert(rec)
    rec.pop('_id')
    return jsonify({'recording': rec}), 201


@app.route('/mobileeg/api/v1/users', methods=['GET'])
@auth.login_required
def get_users():
    users_list = []
    for user in users_collection.find():
        user.pop('_id')
        users_list.append(user)
    return jsonify({'recordings': users_list})


@app.route('/mobileeg/api/v1/users', methods=['POST'])
def create_user():
    if not request.json:
        abort(400)
    user = {
            'username': request.json['username'],
            'password': request.json['password'],
            'birthyear': request.json['birthyear'],
            'gender': request.json['gender'],
            'organization': request.json['organization'],
            'public': request.json['public'],
            'userid': request.json['userid']
            }
    users_collection.insert(user)
    user.pop('_id')
    return jsonify({'user': user}), 201


@app.route('/mobileeg/api/v1/users/<string:username>', methods=['GET'])
@auth.login_required
def get_user(username):
    user = [user for user in users_collection if users_collection['username'] == username]
    if len(user) == 0:
        abort(404)
    return jsonify({'user': user[0]})

"""
@app.route('/mobileeg/api/v1/recordings/<int:recording_id>', methods=['DELETE'])
def delete_recording(recording_id):
    recording = [recording for recording in recordings_collection if recording['id'] == recording_id]
    if len(recording) == 0:
        abort(404)
    recordings_collection.remove(recording[0])
    return jsonify({'result': True})


@app.route('/mobileeg/api/v1/recordings/<int:recording_id>', methods=['GET'])
@auth.login_required
def get_recording(recording_id):
    recording = [recording for recording in recordings_collection if recordings_collection['id'] == recording_id]
    if len(recording) == 0:
        abort(404)
    return jsonify({'recording': recording[0]})
"""


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    app.run(debug=True)