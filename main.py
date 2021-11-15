"""
Norbit fingerprinting backend server.
Runs data fetch script and localization estimation algorithm.
"""
from flask import Flask, jsonify
import pymongo
from flask_restful import abort
from pymongo.errors import DuplicateKeyError
import pandas as pd

from move_data import MoveData
from env import DB_URI, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_CA_FILE
from algorithm_multilateration import Multilateration

# Configure Flask & Flask-PyMongo:
app = Flask(__name__)
CLIENT = None
DB = None
LAST_UPDATE = None
MOVE_DATA = None
BeaconValues = {}

ALGORITHM_VERSIONS = {
    "gateway_pos": "gateway_position",
    "weighted_mean": "weighted_mean",
    "trilat": "trilateration",
    "multilat": "multilateration",
    "fp": "fingerprinting",
}


def abort_beacon_id_not_found(beacon_id):
    """
    Aborts operation if beacon_id is not found
    """
    if beacon_id not in BeaconValues:
        abort(404, message="Beacon Id is not found")


@app.errorhandler(404)
def resource_not_found(error):
    """
    An error-handler to ensure that 404 errors are returned as JSON.
    """
    return jsonify(error=str(error)), 404


@app.errorhandler(DuplicateKeyError)
def dublicate_key_found(error):
    """
    An error-handler to ensure that MongoDB duplicate key errors are returned as JSON.
    """
    return jsonify(error=f"Duplicate key error.{error}"), 400


@app.route('/lastPredictedLocations/', methods=['GET'])
def get_last_predicted_locations():
    """
    Returns the last predicted locations for all beacons with prediction
    data from our database given a device id (beacon id).
    """
    try:
        predicted_locations = DB.calibrationEstimatedPosition.find(
            {'deviceId': {
                "$ne": 41
            }}, {"_id": 0})
    except IndexError:
        print("Index error")
        return "", 404

    data = pd.DataFrame(predicted_locations)

    data = data.sort_values(by=['timestamp'])

    data_multilat = data[data['algorithm'] == ALGORITHM_VERSIONS['multilat']]
    data_fp = data[data['algorithm'] == ALGORITHM_VERSIONS['fp']]

    data_multilat = data_multilat.drop_duplicates(subset='deviceId',
                                                  keep='last')
    data_fp = data_fp.drop_duplicates(subset='deviceId', keep='last')

    data_multilat = data_multilat.drop(
        ['true_latitude', 'true_longitude', 'algorithm', 'timestamp'], axis=1)
    data_fp = data_fp.drop(['algorithm'], axis=1)
    data_multilat = data_multilat.rename(columns={
        'latitude': 'multilat_latitude',
        'longitude': 'multilat_longitude'
    })
    data_fp = data_fp.rename(columns={
        'latitude': 'fp_latitude',
        'longitude': 'fp_longitude'
    })

    data_combined = pd.merge(data_multilat, data_fp, on=['deviceId'])

    return jsonify(data_combined.to_dict(orient='records'))


@app.route('/td/<int:device_id>/', methods=['GET'])
def get_td(device_id: int):
    """
    Returns the telemetry data from our database given a device id (beacon id).
    """
    try:
        telem_data = DB.td.find({"_id": int(device_id)})[0]
    except IndexError:
        print("Index error")
        return "", 404

    BeaconValues[device_id] = telem_data
    return jsonify([telem_data])


@app.route('/update')
def update():
    """
    Updates our database by fetching new data from Norbit Bluetrack database.
    """
    global LAST_UPDATE
    updated_at = MOVE_DATA.update_calibration(1, 41, LAST_UPDATE)
    LAST_UPDATE = updated_at if updated_at != 0 else LAST_UPDATE
    return "Update success", 200


@app.route("/ping", methods=["GET"])
def ping():
    """
    Responds to the ping endpoint with success.
    """
    return "Pong", 200


if __name__ == "__main__":
    CLIENT = pymongo.MongoClient(DB_URI,
                                 port=DB_PORT,
                                 tls=True,
                                 tlsAllowInvalidHostnames=True,
                                 tlsCAFile=DB_CA_FILE,
                                 username=DB_USERNAME,
                                 password=DB_PASSWORD)
    MOVE_DATA = MoveData(CLIENT)
    DB = CLIENT.testdb
    LAST_UPDATE = MOVE_DATA.get_last_updated("calibrationData")
    multilateration = Multilateration(CLIENT, True)
    multilateration.algorithm()
    app.run(debug=True)
    CLIENT.close()
