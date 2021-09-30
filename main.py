import os

from flask import Flask, jsonify, current_app, g
import pymongo
from flask_pymongo import PyMongo
from flask_restful import Resource, abort, reqparse
from pymongo.errors import DuplicateKeyError
from env import *

# Configure Flask & Flask-PyMongo:
app = Flask(__name__)
client = pymongo.MongoClient(DB_URI, port=DB_PORT, tls=True, tlsAllowInvalidHostnames=True,
                             tlsCAFile=DB_CA_FILE, username=DB_USERNAME, password=DB_PASSWORD)
pymongo = PyMongo(app)

beaconValues_put_args = reqparse.RequestParser()
beaconIds = {}

db = client.testdb

td = db.td


class locationSchema(ma.Schema):
    class Meta:
        fields = ("strenger")


def abort_beaconId_not_found(beaconId):
    if beaconId not in beaconIds:
        abort(404, message="Beacon Id is not found")


def abort_beaconId_exists(beaconId):
    if beaconId in beaconIds:
        abort(409, message="Beacon with id already exists")


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


@app.route('/BeaconValues/<string:beaconId>', methods=["GET"])
def get(beaconId):
    abort_beaconId_not_found(beaconId)
    # find kan ta inn parameter til å finne spesifike ting
    # kan bruke blant annet $eq, $ne, $gt, $lt, $lte og $nin
    beaconIds = db.gateway.find()
    return beaconIds[beaconId]


@app.route('/BeaconValues/<string:beaconId>', methods=["PUT"])
def put(beaconId):
    abort_beaconId_exists(beaconId)

    # se på hvilken som er den beste / mest riktig måte å gjøre det på
    args = beaconValues_put_args.parse_args()
    beaconIds[beaconId] = args

    # dette skal være en dict av ting man skal putte inn i collection i mongoDB
    db.gateway.insert_one(beaconId)

    # kan også returnere flask.jsonify(message="success")
    return beaconIds[beaconId], 201


@app.route('/BeaconValues/<string:beaconId>', methods=["DELETE"])
def delete(beaconId):
    abort_beaconId_not_found(beaconId)
    del beaconIds[beaconId]

    db.gateway.delete_one(beaconId)
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)
