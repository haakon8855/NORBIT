import pymongo
import json
from flask import Flask, Response, jsonify, request
from move_data import convert_timestamp
from pprint import pprint


def algorithm(db_client: pymongo.MongoClient):
    """Do stuff"""
    data = db_client.testdb.td.find({"deviceId": 41})[0]
    # for doc in data:
    #     print("")


# tds = convert_timestamp(data)
# tds_filtered = list(filter(lambda td: td["timestamp"] > last_updated, tds))
