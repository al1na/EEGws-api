from flask import Flask, Response, jsonify, request, abort, make_response, redirect, url_for, send_from_directory
from flask.ext.httpauth import HTTPBasicAuth
from bson import json_util
import os
from werkzeug import secure_filename
from pymongo import MongoClient

auth = HTTPBasicAuth()

client = MongoClient()
db = client.testeegdb
recordings_collection = db.recordings
users_collection = db.users

UPLOAD_FOLDER = 'uploaded_recordings'
ALLOWED_EXTENSIONS = set(['bz2'])
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024


rec1 = {
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

user1 = {
        'userid': 'd8f9419e-dbc2-11e4-b9d6-1681e6b88ec1',
        'username': 'al1na',
        'password': 'python',
        'birthyear': 1900,
        'gender': 'F',
        'organization': 'DTU',
        'public': True
        }

#recordings_collection.insert(rec1)
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
    return jsonify({'users': users_list})


@app.route('/mobileeg/api/v1/users', methods=['POST'])
def create_user():
    #TODO: to perform some checks e.g. the userid must be unique
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
    user = users_collection.find({"username": username}, {"_id": 0})
    if user.count() == 0:
        abort(404)
    return jsonify({'user': user[0]})
    #return Response(json_util.dumps({'user': user[0]}), mimetype='application/json')


@app.route('/mobileeg/api/v1/users', methods=['PUT'])
@auth.login_required
def update_user():
    user = users_collection.find({"username": auth.username()})
    if not request.json:
        abort(400)
    if 'password' in request.json and type(request.json['password']) is not unicode:
        abort(400)
    if 'organization' in request.json and type(request.json['organization']) is not unicode:
        abort(400)
    if 'gender' in request.json and request.json['gender'] not in ['F', 'M', 'f', 'm']:
        abort(400)
    if 'birthyear' in request.json and type(request.json['birthyear']) is not int:
        abort(400)
    if 'public' in request.json and type(request.json['public']) is not bool:
        abort(400)
    users_collection.update(
        {"_id": user[0]['_id']},
        {'$set': {'password': request.json.get('password', user[0]['password'])}})
    users_collection.update(
        {"_id": user[0]['_id']},
        {'$set': {'organization': request.json.get('organization', user[0]['organization'])}})
    users_collection.update(
        {"_id": user[0]['_id']},
        {'$set': {'gender': request.json.get('gender', user[0]['gender'])}})
    users_collection.update(
        {"_id": user[0]['_id']},
        {'$set': {'birthyear': request.json.get('birthyear', user[0]['birthyear'])}})
    users_collection.update(
        {"_id": user[0]['_id']},
        {'$set': {'public': request.json.get('public', user[0]['public'])}})
    user = users_collection.find({"username": auth.username()}, {"_id": 0})
    return Response(json_util.dumps({'user': user[0]}), mimetype='application/json')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/mobileeg/api/v1/recordings/upload', methods=['POST'])
@auth.login_required
def handle_uploaded_file():
    print "I am here"
    print len(request.files)
    for x in request.files:
        print x
    file_received = request.files['file']
    if file_received and allowed_file(file_received.filename):
            filename = secure_filename(file_received.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            x = file_received.save(filepath)
            # url_for looks for a function, you pass it the name of the function you are wanting to call
            # http://stackoverflow.com/questions/3683108/flask-error-werkzeug-routing-builderror
            print filepath
            print "compressed " + str(os.path.getsize(filepath))
            decompressedfile = bz2.decompress(filepath)
            print "compressed " + str(os.path.getsize(filepath)) + \
                  " decompressed " + str(os.path.getsize(decompressedfile))
            return redirect(url_for('get_recordings',
                                    filename=filename))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


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