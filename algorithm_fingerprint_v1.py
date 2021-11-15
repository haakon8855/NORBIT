"""
algorithm_fingerprint provides location estimation using fingerprinting
"""
from collections import Counter
from pandas import DataFrame
import pymongo
import numpy as np

from env import DB_URI, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_CA_FILE
from store_fingerprint import get_all_heatmaps

ALG_VER = "fingerprinting"


class FingerprintingV1():
    """
    Estimates the location of a beacon using fingerprinting (v1)
    """
    def __init__(self, db_client: pymongo.MongoClient):
        self.db_client = db_client

    def algorithm(self):
        """
        Returns the predicted location of a beacon fetched from the database.
        """
        # FETCH DATA
        timestamps_test_set = [1633680792, 1633673904, 1633673758]

        for timestamp in timestamps_test_set:
            test_data = DataFrame(
                self.db_client.testdb.callibrationData.find(
                    {'timestamp': timestamp}))

        data = DataFrame(test_data, columns=["gatewayId", "rssi"])
        if data.empty:
            print("No data found for given timestamps.")
            return

        print("Data: \n", data, "\n")
        locator_ids = data["gatewayId"].tolist()

        # FETCH HEATMAP FOR EACH LOCATOR IN DATA
        locators = get_all_heatmaps(locator_ids)
        #print("Locators: ", locators)

        # CALCULATE POSITION
        possible_locations_with_id = {}
        possible_locations = []
        min_values = []

        for i in range(0, len(data)):
            locator_id = data.at[i, "gatewayId"]
            locator_matrix = locators.get(locator_id)
            rssi = data.at[i, "rssi"]
            min_value, closest_indices_list = self.closest_indices(
                locator_matrix, rssi)
            possible_locations_with_id[
                locator_id] = closest_indices_list  # use if no duplicate tuples
            possible_locations += closest_indices_list  # use to find duplicate tuples
            min_values.append(min_value)

            # debug printing
            print(locator_matrix)
            print("id:", locator_id, "rssi:", rssi, "closest indices:",
                  closest_indices_list, "\n")

        print("Possible locations: ",
              possible_locations)  # all possible locations
        #print("min values", min_values) # collection of minimum distances from target value

        # Find most frequent location in list
        res, count = Counter(possible_locations).most_common()[0]

        if count != 1:
            # Return most frequent location
            return res
        else:
            # Find the locator with the smallest difference in rssi
            # value and set this matrix-index to be location
            print("No duplicate locations found.",
                  "Use locator with minimum distance in rssi to estimate.")
            print("Possible locations with id", possible_locations_with_id)
            print("Min values", min_values)
            minimum = min(min_values)
            idx = min_values.index(minimum)
            locator_id = data.at[idx, "gatewayId"]
            res = possible_locations_with_id[locator_id][0]
            return res

    def closest_indices(self, matrix, value):
        """
        Parameters: matrix M and an integer value. Calculates the index/indices in
        the matrix with the closest value to the parameter value.
        Returns the minimum distance between an element
        in M and parameter value and a list with indices.
        """
        dist = np.abs(
            matrix - (np.full(matrix.shape, value, dtype=int))
        )  # find abs difference between M and a matrix filled with value
        min_value = dist.min()
        return min_value, list(zip(*np.where(dist == min_value)))


CLIENT = pymongo.MongoClient(DB_URI,
                             port=DB_PORT,
                             tls=True,
                             tlsAllowInvalidHostnames=True,
                             tlsCAFile=DB_CA_FILE,
                             username=DB_USERNAME,
                             password=DB_PASSWORD)

FINGERPRINTINGV1 = FingerprintingV1(CLIENT)
prediction = FINGERPRINTINGV1.algorithm()
print("Estimated location: ", prediction)

CLIENT.close()
