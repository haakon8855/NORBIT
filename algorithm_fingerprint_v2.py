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
    dist = np.abs(matrix - (np.full(matrix.shape, value, dtype=int)))
    return dist


def tuple_to_square(pos: tuple) -> str:
    """
    Converts from numerical coordinates to alphanumeric coordinates.
    (e.g., (3, 4) -> 'E4' and (2, 1) -> 'C, 2')
    """
    letter_a = ord("a")
    return chr(letter_a + pos[1]) + str(pos[0] + 1)


class FingerprintingV2():
    """
    Estimates the location of a beacon using fingerprinting (v2).
    """
    def __init__(self, db_client: pymongo.MongoClient):
        self.db_client = db_client

    def algorithm(self):
        """
        Returns the predicted location of a beacon fetched from the database.
        """
        (test_data, device_id), true_square = TestFingerprinting.test_e1()
        data = pd.DataFrame(test_data,
                            columns=["gatewayId", "rssi", "timestamp"])
        data["rssi"] = data['rssi'].apply(lambda x: -100 if x <= -90 else x)
        for loc_id in LOCATOR_IDS:
            if not (data["gatewayId"] == str(loc_id)).any():
                data = data.append({
                    'gatewayId': loc_id,
                    "rssi": -100
                },
                                   ignore_index=True)
        if data.empty:
            print("No data found for given timestamps.")
            return

        locator_ids = data["gatewayId"].tolist()

        # FETCH HEATMAP FOR EACH LOCATOR IN DATA
        locators = get_all_heatmaps(locator_ids)

        # CALCULATE POSITION
        dist_values = []

        for i in range(0, len(data)):
            locator_id = data['gatewayId'].iloc[i]
            locator_matrix = locators.get(locator_id)
            rssi = data['rssi'].iloc[i]
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
            "timestamp": int(data["timestamp"].iloc[0]),
            "algorithm": ALG_VER
        }
        # When running in real-time the algorithm will never calibrate the same
        # timestamp twice, thus no need to comment out this line
        # self.db_client.testdb.calibrationEstimatedPosition.insert_one(result)
        return result


class TestFingerprinting():
    """
    Test cases for testing the fingerprinting algorithm (v2)
    """
    @staticmethod
    def test_c1():
        """Test case for square C1 in the parking lot grid"""
        return TestFingerprinting.test_square(14, 1634811600), "c1"

    @staticmethod
    def test_c2():
        """Test case for square C2 in the parking lot grid"""
        return TestFingerprinting.test_square(13, 1634811600), "c2"

    @staticmethod
    def test_c3():
        """Test case for square C3 in the parking lot grid"""
        return TestFingerprinting.test_square(16, 1634811600), "c3"

    @staticmethod
    def test_d1():
        """Test case for square D1 in the parking lot grid"""
        return TestFingerprinting.test_square(16, 1634812800), "d1"

    @staticmethod
    def test_e1():
        """Test case for square E1 in the parking lot grid"""
        return TestFingerprinting.test_square(15, 1634812800), "e1"

    @staticmethod
    def test_square(device_id, timestamp):
        """
        Test case wrapper for running tests on the fingerprinting algorithm.
        Given a device id and timestamp it fetches the telemetry data and
        runs it through the fingerprinting algorithm (v2).
        """
        date_time_from = get_time_stamp_from_unicode(timestamp - 60 * 7)
        date_time_to = get_time_stamp_from_unicode(timestamp - 60 * 3)
        response = API.get_td_by_time_interval(1, device_id + 9,
                                               date_time_from, date_time_to)
        values = pd.DataFrame(convert_timestamp(response))
        values = values.sort_values("timestamp", ascending=False)
        values = values.drop_duplicates(subset="gatewayId", keep="first")
        values["gatewayId"] = values["gatewayId"].apply(str)
        return values, device_id


CLIENT = pymongo.MongoClient(DB_URI,
                             port=DB_PORT,
                             tls=True,
                             tlsAllowInvalidHostnames=True,
                             tlsCAFile=DB_CA_FILE,
                             username=DB_USERNAME,
                             password=DB_PASSWORD)

FINGERPRINTING = FingerprintingV2(CLIENT)
prediction = FINGERPRINTING.algorithm()
print(prediction)

CLIENT.close()
