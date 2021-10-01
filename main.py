from flask import Flask, Response, jsonify, request
import pymongo
from flask_restful import abort
from pymongo.errors import DuplicateKeyError
from env import *

# Configure Flask & Flask-PyMongo:
app = Flask(__name__)
client = pymongo.MongoClient(DB_URI, port=DB_PORT, tls=True, tlsAllowInvalidHostnames=True,
                             tlsCAFile=DB_CA_FILE, username=DB_USERNAME, password=DB_PASSWORD)
BeaconValues = {}
db = client.testdb

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
def post_td(beaconId: int) -> Response:
    new_value = request.get_json()
    BeaconValues[beaconId] = new_value
    db.td.insert_one(new_value)
    return jsonify(message="success"), 201


@app.route('/td/<int:beaconId>', methods=["DELETE"])
def delete_td(beaconId):
    abort_beaconId_not_found(beaconId)
    del BeaconValues[beaconId]

    db.td.delete_many({"_id": beaconId})
    return "", 204

@app.route('/td/<int:deviceId>/', methods=['GET'])
def get_td(deviceId: int) -> Response:
    try:
        td = db.td.find({"_id": int(deviceId)})[0]
    except IndexError:
        print("index error")
        return "", 404
    
    BeaconValues[deviceId] = td
    return jsonify([td])

if __name__ == "__main__":
    for x in db.td.find({}):
        BeaconValues[x["_id"]] = x
    app.run(debug=True)
    client.close()
