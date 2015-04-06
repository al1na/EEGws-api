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


rec1 = {
        'timestamp': 1428262635,
        'device': 'emotiv',
        'electrodes': {'AF3': [10, 20, 33, 12, 56],
                        'O1': [12, 57, 88, 32, 15],
                        'P7': [22, 47, 78, 62, 35]},
        'gyroscope': {'gyroX': [-100, 0, 150, 190, 200], 'gyroY': [-150, -90, 0, 80, 120]},
        'auxdata': {'battery': 100},
        'annotation': u'Blinking experiment 05-04-2015'
        }

rec2 = {
        'timestamp': 1428265342,
        'device': 'emotiv',
        'electrodes': {'AF3': [10, 20, 33, 100, 100],
                        'O1': [12, 57, 88, 100, 100],
                        'P7': [22, 47, 78, 100, 100]},
        'gyroscope': {'gyroX': [-100, 0, 150, 100, 100], 'gyroY': [-150, -90, 0, 100, 100]},
        'auxdata': {'battery': 100},
        'annotation': u'2nd blinking experiment 05-04-2015'
        }

user1 = {
        'id': 'd8f9419e-dbc2-11e4-b9d6-1681e6b88ec1',
        'username': 'al1na',
        'password': 'python',
        'birthyear': 1900,
        'gender': 'F',
        'organization': 'DTU',
        'public': True
        }

#recordings_collection.insert(rec1)
#recordings_collection.insert(rec2)
#users_collection.insert(user1)


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
    recordings_list = []
    for recording in recordings_collection.find():
        recording.pop('_id')
        recordings_list.append(recording)
    return jsonify({'recordings':recordings_list})
    #return Response(json_util.dumps({'page' : recordings_list}), mimetype='application/json')


"""
@app.route('/mobileeg/api/v1/recordings/<int:recording_id>', methods=['GET'])
@auth.login_required
def get_recording(recording_id):
    recording = [recording for recording in recordings_collection if recordings_collection['id'] == recording_id]
    if len(recording) == 0:
        abort(404)
    return jsonify({'recording': recording[0]})
"""


@app.route('/mobileeg/api/v1/recordings', methods=['POST'])
@auth.login_required
def create_task():
    if not request.json:
        abort(400)
    rec = {
            'timestamp': request.json['timestamp'],
            'device': request.json['device'],
            'electrodes': request.json['electrodes'],
            'gyroscope': request.json['gyroscope'],
            'auxdata': request.json['auxdata'],
            'annotation': request.json['annotation']
            }
    recordings_collection.insert(rec)
    rec.pop('_id')
    return jsonify({'recording':rec}), 201


"""
@app.route('/mobileeg/api/v1/recordings/<int:recording_id>', methods=['DELETE'])
def delete_recording(recording_id):
    recording = [recording for recording in recordings_collection if recording['id'] == recording_id]
    if len(recording) == 0:
        abort(404)
    recordings_collection.remove(recording[0])
    return jsonify({'result': True})
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