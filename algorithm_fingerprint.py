#import pymongo
import numpy as np

ALG_VER = "fingerprinting"

test_locator1 = np.array([[-78, -48, -25], [-60, -11, -27], [-60, -40, -18]])
test_locator2 = np.array([[3, 2, -60], [2, 1, 1], [1, 1, 2]])

test_data = np.array([{"locator_id": 1, "rssi": -20},
                     {"locator_id": 2, "rssi": -60}])


def algorithm_fingerprinting():
    """
    Calculates predicted location for all beacons with updates. Then stores
    the predicted locations in the database.
    """

    # list of tuples
    possible_locations = []

    for data in range(0, len(test_data)):
        if test_data[data]["locator_id"] == 1:
            square = find_nearest(test_locator1, test_data[data]["rssi"])
            print("square", square)
            #possible_locations.append((square[0][0], square[1][0]))
            #print("possible loc", possible_locations)
        # elif test_data[data]["locator_id"] == 2:
            #square = np.where(test_locator2 == test_data[data]["rssi"])
            #possible_locations.append((square[0][0], square[1][0]))


def find_nearest(array, value):
    best_val_in_row = []
    best_idx_in_row = []
    for row in array:
        array = np.asarray(row)
        best_row_idx = (np.abs(row - value)).argmin()
        best_idx_in_row.append(best_row_idx)
        best_val_in_row.append((array[best_row_idx]))

    best_array = np.asarray(best_val_in_row)
    best_idx = (np.abs(best_array - value)).argmin()
    row = array[best_idx]

    return best_idx, best_idx_in_row


algorithm_fingerprinting()
