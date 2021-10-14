from flask import Flask, Response, jsonify, request
import pymongo
import move_data
from flask_restful import abort
from pymongo.errors import DuplicateKeyError
from env import *

# Configure Flask & Flask-PyMongo:
app = Flask(__name__)
CLIENT = None
DB = None
LAST_UPDATE = None
BeaconValues = {}

def abort_beaconId_not_found(beaconId):
    if beaconId not in BeaconValues:
        abort(404, message="Beacon Id is not found")


@app.errorhandler(404)
def resource_not_found(e):
    """
    An error-handler to ensure that 404 errors are returned as JSON.
    """
    return jsonify(error=str(e)), 404


@app.errorhandler(DuplicateKeyError)
def resource_not_found(e):
    """
    An error-handler to ensure that MongoDB duplicate key errors are returned as JSON.
    """
    return jsonify(error=f"Duplicate key error."), 400


@app.route('/td/<int:beaconId>', methods=["POST"])
def post_td(beaconId: int):
    new_value = request.get_json()
    BeaconValues[beaconId] = new_value
    DB.td.insert_one(new_value)
    return jsonify(message="success"), 201


@app.route('/td/<int:beaconId>', methods=["DELETE"])
def delete_td(beaconId):
    abort_beaconId_not_found(beaconId)
    del BeaconValues[beaconId]

    DB.td.delete_many({"_id": beaconId})
    return "", 204


@app.route('/td/<int:deviceId>/', methods=['GET'])
def get_td(deviceId: int):
    try:
        td = DB.td.find({"_id": int(deviceId)})[0]
    except IndexError:
        print("index error")
        return "", 404
    
    BeaconValues[deviceId] = td
    return jsonify([td])


@app.route('/update')
def update():
    global LAST_UPDATE
    updated_at = move_data.update_callibration(CLIENT, 1, 41, LAST_UPDATE)
    LAST_UPDATE = updated_at if updated_at != 0 else LAST_UPDATE
    return "sucess", 200

@app.route("/ping", methods=["GET"])
def ping():
    return "sucess", 200


if __name__ == "__main__":
    CLIENT = pymongo.MongoClient(DB_URI, port=DB_PORT, tls=True, tlsAllowInvalidHostnames=True,
                             tlsCAFile=DB_CA_FILE, username=DB_USERNAME, password=DB_PASSWORD)
    DB = CLIENT.testdb
    LAST_UPDATE = move_data.get_last_updated(CLIENT, "callibrationData")
    app.run(debug=True)
    CLIENT.close()
