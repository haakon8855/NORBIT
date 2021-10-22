import pymongo
from pandas import DataFrame
import numpy as np
from collections import Counter
from store_fingerprint import get_all_heatmaps
from norbit_api import NorbitApi

import move_data
from env import DB_URI, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_CA_FILE

ALG_VER = "fingerprinting"

def closest_indices(M, value):
    """
    Parameters: matrix M and an integer value. Calculates the index/indices in the matrix with 
    the closest value to the parameter value. Returns the minimum distance between an element
    in M and parameter value and a list with indices.
    """
    D = np.abs(M - (np.full(M.shape, value, dtype=int))) # find abs difference between M and a matrix filled with value
    min_value = D.min()
    return min_value, list(zip(*np.where(D == min_value))) 


def algorithm_fingerprinting(db_client: pymongo.MongoClient):

    """
    Estimates the location of a beacon using fingerprinting
    """

    # FETCH DATA
    timestamps_test_set = [1633680792, 1633673904, 1633673758]

    for timestamp in timestamps_test_set:
        test_data = DataFrame(
            db_client.testdb.callibrationData.find(
                {'timestamp': timestamp}))

    df = DataFrame(test_data, columns=["gatewayId", "rssi"])
    if(df.empty):
        print("No data found for given timestamps.")
        return  

    print("Data: \n", df, "\n")
    locator_ids = df["gatewayId"].tolist()

    # FETCH HEATMAP FOR EACH LOCATOR IN DATA
    locators = get_all_heatmaps(locator_ids)
    #print("Locators: ", locators)


    # CALCULATE POSITION
    possible_locations_with_id = {}
    possible_locations = []
    min_values = []

    for i in range(0, len(df)):
        locator_id = df.at[i, "gatewayId"]
        locator_matrix = locators.get(locator_id)
        rssi = df.at[i, "rssi"]
        min_value, closest_indices_list = closest_indices(locator_matrix, rssi)
        possible_locations_with_id[locator_id] = closest_indices_list # use if no duplicate tuples
        possible_locations += closest_indices_list  # use to find duplicate tuples
        min_values.append(min_value)

        # debug printing
        print(locator_matrix)
        print("id:", locator_id, "rssi:", rssi, "closest indices:", closest_indices_list, "\n")

    print("Possible locations: ", possible_locations) # all possible locations
    #print("min values", min_values) # collection of minimum distances from target value

    # Find most frequent location in list
    res, count = Counter(possible_locations).most_common()[0]

    if count != 1:
        # return most frequent location
        return res
    else:
        # find the locator with the smallest difference in rssi value and set this matrix-index to be location
        print("No duplicate locations found. Use locator with minimum distance in rssi to estimate.")
        print("Possible locations with id", possible_locations_with_id)
        print("Min values", min_values)
        minimum = min(min_values)
        idx = min_values.index(minimum)
        locator_id = df.at[idx, "gatewayId"]
        res = possible_locations_with_id[locator_id][0]
        return res


CLIENT = pymongo.MongoClient(DB_URI,
                                port=DB_PORT,
                                tls=True,
                                tlsAllowInvalidHostnames=True,
                                tlsCAFile=DB_CA_FILE,
                                username=DB_USERNAME,
                                password=DB_PASSWORD)

location = algorithm_fingerprinting(CLIENT)
print("Estimated location: ", location)

CLIENT.close()