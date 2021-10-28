"""
algorithm_fingerprint_v2 provides location estimation using fingerprinting
"""

import pymongo
import pandas as pd
import numpy as np

from env import DB_URI, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_CA_FILE
from move_data import convert_timestamp
from store_fingerprint import get_all_heatmaps
from norbit_api import NorbitApi, get_time_stamp_from_unicode
from coords import coords

ALG_VER = "fingerprinting"
LOCATOR_IDS = [7, 8, 9, 10, 11, 12]

API = NorbitApi()
COORDS = coords


def distance_matrix(matrix, value):
    """
    Returns the abs difference between M and a matrix filled with value
    """
    dist = np.abs(
        matrix - (np.full(matrix.shape, value, dtype=int))
    )  # find abs difference between M and a matrix filled with value
    return dist


def test_C1():
    return test_square(14, 1634811600), "c1"


def test_C2():
    return test_square(13, 1634811600), "c2"


def test_C3():
    return test_square(16, 1634811600), "c3"


def test_D1():
    return test_square(16, 1634812800), "d1"


def test_E1():
    return test_square(15, 1634812800), "e1"


def test_square(device_id, timestamp):
    date_time_from = get_time_stamp_from_unicode(timestamp - 60 * 7)
    date_time_to = get_time_stamp_from_unicode(timestamp - 60 * 3)
    response = API.get_td_by_time_interval(1, device_id + 9, date_time_from,
                                           date_time_to)
    values = pd.DataFrame(convert_timestamp(response))
    values = values.sort_values("timestamp", ascending=False)
    values = values.drop_duplicates(subset="gatewayId", keep="first")
    print(values["gatewayId"])
    values["gatewayId"] = values["gatewayId"].apply(str)
    return values, device_id


def tuple_to_square(pos: tuple) -> str:
    a = ord("a")
    return chr(a + pos[1]) + str(pos[0] + 1)


def algorithm_fingerprinting(db_client: pymongo.MongoClient):
    """
    Estimates the location of a beacon using fingerprinting
    """
    (test_data, device_id), true_square = test_E1()
    df = pd.DataFrame(test_data, columns=["gatewayId", "rssi", "timestamp"])
    df["rssi"] = df['rssi'].apply(lambda x: -100 if x <= -90 else x)
    for loc_id in LOCATOR_IDS:
        if not (df["gatewayId"] == str(loc_id)).any():
            df = df.append({
                'gatewayId': loc_id,
                "rssi": -100
            },
                           ignore_index=True)
    if (df.empty):
        print("No data found for given timestamps.")
        return

    locator_ids = df["gatewayId"].tolist()

    # FETCH HEATMAP FOR EACH LOCATOR IN DATA
    locators = get_all_heatmaps(locator_ids)

    # CALCULATE POSITION
    dist_values = []

    for i in range(0, len(df)):
        locator_id = df['gatewayId'].iloc[i]
        locator_matrix = locators.get(locator_id)
        rssi = df['rssi'].iloc[i]
        dist_values.append(distance_matrix(locator_matrix, rssi))

    dist_values = np.array(dist_values).astype(float)
    for i in range(len(dist_values)):
        dist_values[i][dist_values[i] > 500] = np.nan
        dist_values[i] = np.square(dist_values[i])

    mean_error = np.nanmean(dist_values, axis=0)
    mean_prob = np.power(np.nanmax(mean_error), 0.0001) - np.power(
        mean_error, 0.0001)
    mean_prob = mean_prob / np.nansum(mean_prob)

    estimated_square = list(
        zip(*np.where(mean_error == np.nanmin(mean_error))))

    estimated_location = coords[tuple_to_square(estimated_square[0])]
    true_location = coords[true_square]
    result = {
        "deviceId": device_id,
        "latitude": estimated_location[0],
        "longitude": estimated_location[1],
        "true_latitude": true_location[0],
        "true_longitude": true_location[1],
        "timestamp": int(df["timestamp"].iloc[0]),
        "algorithm": ALG_VER
    }
    # db_client.testdb.calibrationEstimatedPosition.insert_one(result)


CLIENT = pymongo.MongoClient(DB_URI,
                             port=DB_PORT,
                             tls=True,
                             tlsAllowInvalidHostnames=True,
                             tlsCAFile=DB_CA_FILE,
                             username=DB_USERNAME,
                             password=DB_PASSWORD)

algorithm_fingerprinting(CLIENT)

CLIENT.close()
