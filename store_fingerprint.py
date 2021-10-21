import pymongo
import random

from pymongo.common import HEARTBEAT_FREQUENCY
import numpy as np
from env import *

CLIENT = pymongo.MongoClient(DB_URI,
                            port=DB_PORT,
                            tls=True,
                            tlsAllowInvalidHostnames=True,
                            tlsCAFile=DB_CA_FILE,
                            username=DB_USERNAME,
                            password=DB_PASSWORD)
LETTERS = range(ord("a"), ord("f"))
NUMBERS = range(5)

def create_random_fingerprint():
    fingerprint = {}
    locator_ids = np.array([8, 12, 7, 10, 11, 9])
    for char in LETTERS:
        for i in NUMBERS:
            square_name = chr(char) + str(i)
            fingerprint[square_name] = {}
            locators = np.random.choice(locator_ids, random.randint(1, len(locator_ids)-1))
            for locator in locators:
                fingerprint[square_name][str(locator)] = random.randint(-100, -20)
            
    CLIENT.testdb.fingerprint.insert_one(fingerprint)

def get_fingerprint(fingerprint_id: int) -> dict:
    fingerprint = CLIENT.testdb.fingerprint.find_one()
    return fingerprint

def create_heatmap(locator_id: int, fingerprint_id=0) -> list:
    fingerprint = get_fingerprint(fingerprint_id)
    heatmap = []
    for letter in LETTERS:
        row = []
        for i in NUMBERS:
            cell = fingerprint[chr(letter) + str(i)]
            val = cell[str(locator_id)] if str(locator_id) in cell else 0
            row.append(val)

        heatmap.append(row)
    
    return np.array(heatmap)

def get_all_heatmaps(locator_ids):
    heatmaps = {}
    for id in locator_ids:
        heatmaps[locator_ids] = create_heatmap(id)
    
    return heatmaps

if __name__ == "__main__":
    print(create_heatmap(1, 11))
    # create_random_fingerprint()
    CLIENT.close()
