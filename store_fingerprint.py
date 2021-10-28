import pymongo
import random
import datetime
import numpy as np
import pandas as pd
from env import *
from norbit_api import NorbitApi, get_time_stamp_from_unicode
from map_squares import map_squares
from move_data import convert_timestamp

CLIENT = pymongo.MongoClient(DB_URI,
                             port=DB_PORT,
                             tls=True,
                             tlsAllowInvalidHostnames=True,
                             tlsCAFile=DB_CA_FILE,
                             username=DB_USERNAME,
                             password=DB_PASSWORD)
LETTERS = range(ord("a"), ord("h") + 1)
NUMBERS = range(1, 5)
API = NorbitApi()
SQUARES = map_squares
COLUMNS = ["gatewayId", "rssi", "timestamp"]


def create_random_fingerprint():
    fingerprint = {}
    locator_ids = np.array([8, 12, 7, 10, 11, 9])
    for char in NUMBERS:
        for i in LETTERS:
            square_name = chr(char) + str(i)
            fingerprint[square_name] = {}
            locators = np.random.choice(
                locator_ids, random.randint(1,
                                            len(locator_ids) - 1))
            for locator in locators:
                fingerprint[square_name][str(locator)] = random.randint(
                    -100, -20)

    CLIENT.testdb.fingerprint.insert_one(fingerprint)


def get_square_values(square):
    deviceId, timestamp = SQUARES[square]
    date_time_from = get_time_stamp_from_unicode(timestamp - 121)
    date_time_to = get_time_stamp_from_unicode(timestamp + 121)
    response = API.get_td_by_time_interval(1, deviceId + 9, date_time_from,
                                           date_time_to)
    values = pd.DataFrame(convert_timestamp(response))
    if values.empty:
        return {}
    values = values[COLUMNS]
    values = values.sort_values("timestamp", ascending=False)
    values = values.drop_duplicates(subset="gatewayId", keep="first")
    values["gatewayId"] = values["gatewayId"].apply(str)
    return values.set_index("gatewayId").T.to_dict()


def create_fingerprint():
    global SQUARES
    fingerprint = {}
    for square in SQUARES.keys():
        fingerprint[square] = get_square_values(square)
    CLIENT.testdb.fingerprint.insert_one(fingerprint)


def get_fingerprint(fingerprint_id: int) -> dict:
    fingerprint = CLIENT.testdb.fingerprint.find_one()
    return fingerprint


def create_heatmap(locator_id: int, fingerprint_id=0) -> list:
    fingerprint = get_fingerprint(fingerprint_id)
    heatmap = []
    for i in NUMBERS:
        row = []
        for letter in LETTERS:
            cell_name = chr(letter) + str(i)
            if cell_name in fingerprint:
                cell = fingerprint[cell_name]
            else:
                cell = {}
            val = cell[str(locator_id)]["rssi"] if str(
                locator_id) in cell else -1000
            row.append(val)

        heatmap.append(row)

    return np.array(heatmap)


def get_all_heatmaps(locator_ids):
    heatmaps = {}
    for id in locator_ids:
        heatmaps[id] = create_heatmap(id)

    return heatmaps


if __name__ == "__main__":
    # print(create_heatmap(11))
    # create_random_fingerprint()
    # print(get_square_values("g3"))
    # create_fingerprint()
    print(get_all_heatmaps([8, 12, 7, 10, 11, 9]))
    CLIENT.close()
