import pymongo
import pandas as pd
import numpy as np
from collections import Counter

from env import DB_URI, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_CA_FILE
from move_data import convert_timestamp
from store_fingerprint import get_all_heatmaps
from norbit_api import NorbitApi, get_time_stamp_from_unicode

ALG_VER = "fingerprinting"
LOCATOR_IDS = [7, 8, 9, 10, 11, 12]

API = NorbitApi()


def distance_matrix(M, value):
    """
    Returns the abs difference between M and a matrix filled with value
    """
    D = np.abs(
        M - (np.full(M.shape, value, dtype=int))
    )  # find abs difference between M and a matrix filled with value
    return D


def test_C1():
    return test_square(14, 1634811600)


def test_C2():
    return test_square(13, 1634811600)


def test_C3():
    return test_square(16, 1634811600)


def test_D1():
    return test_square(16, 1634812800)


def test_E1():
    return test_square(15, 1634812800)


def test_square(device_id, timestamp):
    columns = ["gatewayId", "rssi", "timestamp"]
    date_time_from = get_time_stamp_from_unicode(timestamp - 60 * 7)
    date_time_to = get_time_stamp_from_unicode(timestamp - 60 * 3)
    response = API.get_td_by_time_interval(1, device_id + 9, date_time_from,
                                           date_time_to)
    values = pd.DataFrame(convert_timestamp(response))
    values = values[columns]
    values = values.sort_values("timestamp", ascending=False)
    values = values.drop_duplicates(subset="gatewayId", keep="first")
    print(values["gatewayId"])
    values["gatewayId"] = values["gatewayId"].apply(str)
    return values


def algorithm_fingerprinting(db_client: pymongo.MongoClient):
    """
    Estimates the location of a beacon using fingerprinting
    """

    # FETCH DATA
    timestamps_test_set = [1633680792, 1633673904, 1633673758]

    for timestamp in timestamps_test_set:
        test_data = pd.DataFrame(
            db_client.testdb.callibrationData.find({'timestamp': timestamp}))
        test_data = test_E1()
        df = pd.DataFrame(test_data, columns=["gatewayId", "rssi"])
        print("Håkon", type(df['gatewayId'].iloc[0]))
        for loc_id in LOCATOR_IDS:
            if str(loc_id) not in df['gatewayId']:
                df = df.append({
                    'gatewayId': loc_id,
                    "rssi": -100
                },
                               ignore_index=True)
        if (df.empty):
            print("No data found for given timestamps.")
            return

        print(df)

        # print("Data: \n", df, "\n")
        locator_ids = df["gatewayId"].tolist()

        # FETCH HEATMAP FOR EACH LOCATOR IN DATA
        locators = get_all_heatmaps(locator_ids)

        # CALCULATE POSITION
        dist_values = []

        for i in range(0, len(df)):
            # locator_id = df.at[i, "gatewayId"]
            locator_id = df['gatewayId'].iloc[i]
            locator_matrix = locators.get(locator_id)
            rssi = df['rssi'].iloc[i]
            dist_values.append(distance_matrix(locator_matrix, rssi))

            # debug printing
            # print(locator_matrix)
            # print("id:", locator_id, "rssi:", rssi, "\n")

        dist_values = np.array(dist_values).astype(float)
        for i in range(len(dist_values)):
            dist_values[i][dist_values[i] > 500] = np.nan
            dist_values[i] = np.square(dist_values[i])

        mean_error = np.nanmean(dist_values, axis=0)
        estimated_location = list(
            zip(*np.where(mean_error == np.nanmin(mean_error))))
        # print("\n\nTrue loc", test_data.positionLat, test_data.positionLng)
        print("Pred loc", estimated_location)
        return estimated_location

    return estimated_location


CLIENT = pymongo.MongoClient(DB_URI,
                             port=DB_PORT,
                             tls=True,
                             tlsAllowInvalidHostnames=True,
                             tlsCAFile=DB_CA_FILE,
                             username=DB_USERNAME,
                             password=DB_PASSWORD)

location = algorithm_fingerprinting(CLIENT)
#print("Estimated location: ", location)

CLIENT.close()