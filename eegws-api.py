import matplotlib
import os
import bz2
import json
import pandas as pd
import numpy as np
from flask import Flask, Response, jsonify, request, abort, make_response, redirect, url_for, send_from_directory
from flask.ext.httpauth import HTTPBasicAuth
from bson import json_util
from bson.objectid import ObjectId
from werkzeug import secure_filename
from pymongo import MongoClient
from pylab import *
from matplotlib import pyplot as plt
from matplotlib import mlab


ALL_ELECTRODES = ['AF3', 'AF4', 'AF7', 'AF8', 'AFz', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'CP1', 'CP2', 'CP3', 'CP4', 'CP5',
              'CP6', 'CPz', 'Cz', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'FC1', 'FC2', 'FC3', 'FC4', 'FC5',
              'FC6', 'FCz', 'FP1', 'FP2', 'Fpz', 'FT7', 'FT8', 'Fz', 'Iz', 'Nz', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6',
              'P7', 'P8', 'PO3', 'PO4', 'PO7', 'PO8', 'POz', 'Pz', 'O1', 'O2', 'Oz', 'T7', 'T8', 'T9', 'T10', 'TP7',
              'TP8', 'TP9', 'TP10']
ELECTRODES = ['P7', 'AF3', 'O1', 'P8', 'FC6']

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
        'sampling_rate': 128,
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


def convert_recording_to_pandas_dataframe(rec):
    dict = {'timestamp': rec['timestamp']}
    for electrode in rec['electrodes'].keys():
        dict[electrode] = rec['electrodes'][electrode]
    data = pd.DataFrame(dict)
    data[['timestamp'] + rec['electrodes'].keys()]
    return data


@auth.get_password
def get_password(username):
    user = users_collection.find({"username": username}, {"password": 1, "_id": 0})
    if user.count() == 0:
        abort(404)
    for u in user:
        password = u.get('password')
    return password


def find_recording_by_id(recording_id):
    recording = recordings_collection.find({"_id": ObjectId(recording_id)})
    return recording[0]


def find_recordings_db(annotation=None):
    recordings_list = []
    if annotation is not None:
        for recording in recordings_collection.find({"annotation": annotation}, {"_id": 0}):
            recordings_list.append(recording)
    else:
        for recording in recordings_collection.find():
            recording.pop('_id')
            recordings_list.append(recording)
    return recordings_list


@app.route('/mobileeg/api/v1/recordings', methods=['GET'])
@auth.login_required
def get_recordings():
    #TODO: to provide only the public recordings (check if public=True for the user)
    recordings_list = []
    if request.args.get("annotation"):
        for recording in recordings_collection.find({"annotation": request.args.get("annotation")}, {"_id": 0}):
            recordings_list.append(recording)
    else:
        for recording in recordings_collection.find():
            recording.pop('_id')
            recordings_list.append(recording)
    return jsonify({'recordings': recordings_list})


def find_userid_db(username):
    user = users_collection.find({"username": username})
    for u in user:
        userid = u.get('userid')
    return userid

@app.route('/mobileeg/api/v1/recordings', methods=['POST'])
@auth.login_required
def create_recording():
    global userid
    if not request.json:
        abort(400)
    userid = find_userid_db(auth.username())
    rec = {
            'timestamp': request.json['timestamp'],
            'device': request.json['device'],
            'sampling_rate': request.json['sampling_rate'],
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


@app.route('/mobileeg/api/v1/users/<string:username>/recordings', methods=['GET'])
@auth.login_required
def get_user_recordings(username):
    user = users_collection.find({"username": username, "public": True})
    user_id = user[0]['userid']
    user_recordings = []
    if request.args.get("annotation"):
        print request.args.get("annotation")
        for recording in recordings_collection.find({"$and": [{"userid": user_id},
                                                              {"annotation": request.args.get("annotation")}]},
                                                    {"_id": 0}):
            user_recordings.append(recording)
    else:
        for recording in recordings_collection.find({"userid": user_id}, {"_id": 0}):
            user_recordings.append(recording)
    return jsonify({'user recordings': user_recordings})


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/mobileeg/api/v1/recordings/<string:recording_id>/timeseriesplot', methods=['GET'])
@auth.login_required
def create_timeseries_plot(recording_id):
    #TODO: To improve.
    electrode = request.args.get("electrode")
    recording = find_recording_by_id(recording_id)
    if electrode not in ELECTRODES or recording is None:
        abort(404)
    plt.figure(figsize=(6, 8))
    for electrode in recording['electrodes']:
        if len(recording['timestamp']) == len(recording['electrodes'][electrode]):
            plt.plot(recording['timestamp'], recording['electrodes'][electrode], 'b-')
    plt.xlabel("time")
    plt.ylabel("signal magnitude")
    plot_filename = "timeseries_" + recording_id + "_" + electrode + ".png"
    plt.savefig(plot_filename, dpi=150)
    return send_from_directory(app.root_path, plot_filename)


@app.route('/mobileeg/api/v1/recordings/<string:recording_id>/spectrogram', methods=['GET'])
@auth.login_required
def create_spectrogram(recording_id):
    electrode = request.args.get("electrode")
    recording = find_recording_by_id(recording_id)
    if electrode not in ELECTRODES or recording is None:
        abort(404)
    plt.figure(figsize=(6, 8))
    specgram(recording['electrodes'][electrode], Fs=recording['sampling_rate'], NFFT=512)
    plot_filename = "spectrogram_" + recording_id + "_" + electrode + ".png"
    plt.savefig(plot_filename, dpi=150)
    return send_from_directory(app.root_path, plot_filename)


@app.route('/mobileeg/api/v1/recordings/<string:recording_id>/peakfrequency', methods=['GET'])
@auth.login_required
def calculate_peak_frequency(recording_id):
    electrode = request.args.get("electrode")
    recording = find_recording_by_id(recording_id)
    if electrode not in ELECTRODES or recording is None:
        abort(404)
    fourier = np.fft.fft(recording['electrodes'][electrode])
    freqs = np.fft.fftfreq(len(recording['electrodes'][electrode]), 1/float(recording['sampling_rate']))
    magnitudes = abs(fourier[np.where(freqs >= 0)])
    peak_frequency = np.argmax(magnitudes)
    print peak_frequency
    return str(peak_frequency)



@app.route('/mobileeg/api/v1/recordings/<string:recording_id>/powerspectraldensity', methods=['GET'])
@auth.login_required
def calculate_psd(recording_id):
    electrode = request.args.get("electrode")
    recording = find_recording_by_id(recording_id)
    if electrode not in ELECTRODES or recording is None:
        abort(404)
    #print recording['sampling_rate']
    #print recording['electrodes'][electrode]
    psd = mlab.psd(recording['electrodes'][electrode], Fs=recording['sampling_rate'], NFFT=128)
    plt.figure(figsize=(6, 8))
    plt.plot(psd[1], psd[0], 'b-')
    plt.xlabel("FREQUENCY")
    plt.ylabel("POWER SPECTRAL DENSITY")
    plot_filename = "psd_" + recording_id + "_" + electrode + ".png"
    plt.savefig(plot_filename, dpi=150)
    return send_from_directory(app.root_path, plot_filename)


@app.route('/mobileeg/api/v1/recordings/<string:recording_id>/magnitudespectrum', methods=['GET'])
@auth.login_required
def plot_magnitude_spectrum(recording_id):
    electrode = request.args.get("electrode")
    recording = find_recording_by_id(recording_id)
    if electrode not in ELECTRODES or recording is None:
        abort(404)
    fourier = np.fft.fft(recording['electrodes'][electrode])
    freqs = np.fft.fftfreq(len(recording['electrodes'][electrode]), 1/float(recording['sampling_rate']))
    positive_freqs = freqs[np.where(freqs >= 0)]
    magnitudes = abs(fourier[np.where(freqs >= 0)])
    plt.figure(figsize=(6, 8))
    plt.plot(positive_freqs, magnitudes, 'g-')
    plt.ylabel("POWER")
    plt.xlabel("FREQUENCY")
    plot_filename = "magnitude_spectrum_" + recording_id + "_" + electrode + ".png"
    plt.savefig(plot_filename, dpi=150)
    return send_from_directory(app.root_path, plot_filename)


@app.route('/mobileeg/api/v1/recordings/upload', methods=['POST'])
@auth.login_required
def handle_uploaded_file():
    file_received = request.files['file']
    if file_received and allowed_file(file_received.filename):
            filename = secure_filename(file_received.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file_received.save(filepath)
            decompressed_data = unpack_data(filepath)
            json_data = load_data_as_json(decompressed_data)
            rec = insert_recording(json_data, auth.username())
            return jsonify(rec), 201


def unpack_data(filepath):
    if os.path.getsize(filepath) > 5 * 1024 * 1024:
        decompressed_file = decompress_file_bzip(filepath)
        decompressed_data = open(decompressed_file, 'r')
    else:
        decompressed_data = bz2.BZ2File(filepath).read()
    return decompressed_data


def load_data_as_json(decompressed_data):
    #  http://stackoverflow.com/questions/23344948/python-validate-and-format-json-files
    json_data = json.loads(decompressed_data)
    return json_data


def insert_recording(rec_json, username):
    userid = find_userid_db(username)
    rec_json['userid'] = userid
    recordings_collection.insert(rec_json)
    rec_json.pop('_id')
    return rec_json


def decompress_file_bzip(filepath):
    """
    Useful for big files (the decompression is sequential)
    """
    decompress_file_path = os.path.join(filepath + '.decompressed')
    with open(decompress_file_path, 'wb') as new_file, open(filepath, 'rb') as file:
        decompressor = bz2.BZ2Decompressor()
        for data in iter(lambda: file.read(100 * 1024), b''):
            new_file.write(decompressor.decompress(data))
    return decompress_file_path


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