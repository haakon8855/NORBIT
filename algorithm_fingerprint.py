#import pymongo
from pandas import DataFrame
import numpy as np

ALG_VER = "fingerprinting"

test_locator1 = np.array([[-78, -48, -25], [-60, -11, -27], [-60, -18, -16]])
test_locator2 = np.array([[3, 2, -60], [2, 1, 1], [1, 1, 2]])

test_data = np.array([{"locator_id": 1, "rssi": -20},
                     {"locator_id": 2, "rssi": -60}])


M_test = np.array([[1,-1,2,-2,3],[1,-1,2,-2,3]])

def closest_indices(M,value):
    D = np.abs(M - (np.full(M.shape,value,dtype=int)))
    min_value = D.min()
    return list(zip(*np.where(D==min_value)))


indices = closest_indices(test_locator1,-20)
print(indices)



def algorithm_fingerprinting():

    # list of tuples
    possible_locations = []

    for data in range(0, len(test_data)):
        #if test_data[data]["locator_id"] == 1:
        #elif test_data[data]["locator_id"] == 2:
        continue

algorithm_fingerprinting()