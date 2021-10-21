#import pymongo
from pandas import DataFrame
import numpy as np
from collections import Counter

ALG_VER = "fingerprinting"

# For testing, should fetch test_data from database
test_data = [[1, -20], [3, -60], [4, -50], [6, -65]]
df = DataFrame(test_data, columns=["locator_id", "rssi"])


# For testing, should fetch these matrices from database
test_locator1 = np.array([[-78, -48, -25], [-60, -11, -27], [-60, -18, -16]])
test_locator3 = np.array([[-45, -20, -60], [-46, -60, -47], [-67, -38, -50]])
test_locator4 = np.array([[-50, -28, -50], [-45, -60, -50], [-49, -42, -65]])
test_locator6 = np.array([[-38, -20, -70], [-58, -45, -59], [-28, -48, -46]])

# Should be in this format, fetched from database. Dictionary with id and corresponding matrix
locators = {1: test_locator1, 3: test_locator3, 4:test_locator4, 6:test_locator6}


def closest_indices(M,value):
    D = np.abs(M - (np.full(M.shape,value,dtype=int)))
    min_value = D.min()
    return min_value, list(zip(*np.where(D==min_value)))


def algorithm_fingerprinting():

    possible_locations_with_id = {}
    possible_locations = []
    min_values = []

    for i in range(0, len(df)):
        locator_id = df.at[i, "locator_id"]
        locator_matrix = locators.get(locator_id)
        #print(locator_matrix)
        rssi = df.at[i, "rssi"]
        min_value, closest_indices_list = closest_indices(locator_matrix, rssi)
        possible_locations_with_id[locator_id] = closest_indices_list #use if no duplicate tuples
        possible_locations += closest_indices_list #use to find duplicate tuples
        min_values.append(min_value)
        #print("id:", locator_id, "rssi:", rssi, "closest indices:", closest_indices_list, "\n")

    print("possible locations: ", possible_locations)
    print("min values", min_values)
    
    # Find most frequent location in list
    res = Counter(closest_indices_list).most_common()[0][0]
    print("res", res)

    if len(res) != 0:
        # return most frequent location
        return res
    else:
        # find the locator with the smallest difference in rssi value and set this matrix-index to be location
        minimum = min(min_values)
        idx = min_values.index(minimum)
        locator_id = df.at[idx, "locator_id"]
        res = possible_locations_with_id[locator_id][0]
    

algorithm_fingerprinting()