"""
store_fingerprint fetches calibration data from NORBIT's database,
creates a fingerprint from this data, and stores it in our own database.
"""
import random
import pymongo
import numpy as np
import pandas as pd
from data_processing.norbit_api import NorbitApi, get_time_stamp_from_unicode
from data_processing.move_data import MoveData
from env import DB_URI, DB_PORT, DB_CA_FILE, DB_USERNAME, DB_PASSWORD
from data.map_squares import map_squares


class StoreFingerprint():
    """
    Stores a fingerprint to our database by fetching calibration data from
    NORBIT's database.
    """
    def __init__(self, db_client: pymongo.MongoClient):
        self.db_client = db_client
        self.numbers = range(1, 5)
        self.squares = map_squares
        self.columns = ["gatewayId", "rssi", "timestamp"]
        self.letters = range(ord("a"), ord("h") + 1)
        self.api = NorbitApi()

    def get_square_values(self, square):
        """
        Fetches values from each cell in the calibration grid.
        """
        device_id, timestamp = self.squares[square]
        date_time_from = get_time_stamp_from_unicode(timestamp - 121)
        date_time_to = get_time_stamp_from_unicode(timestamp + 121)
        response = self.api.get_td_by_time_interval(1, device_id + 9,
                                                    date_time_from,
                                                    date_time_to)
        values = pd.DataFrame(MoveData.convert_timestamp(response))
        if values.empty:
            return {}
        values = values[self.columns]
        values = values.sort_values("timestamp", ascending=False)
        values = values.drop_duplicates(subset="gatewayId", keep="first")
        values["gatewayId"] = values["gatewayId"].apply(str)
        return values.set_index("gatewayId").T.to_dict()

    def create_fingerprint(self):
        """
        Creates the fingerprint datastructure from individual calibration data
        from each square in the calibration grid.
        """
        fingerprint = {}
        for square in self.squares.keys():
            fingerprint[square] = self.get_square_values(square)
        self.db_client.testdb.fingerprint.insert_one(fingerprint)

    def get_fingerprint(self, fingerprint_id: int) -> dict:
        """
        Fetches a specific fingerprint from the database.
        Currently this always fetches the newest fingerprint.
        """
        fingerprint = self.db_client.testdb.fingerprint.find_one()
        return fingerprint

    def create_heatmap(self, locator_id: int, fingerprint_id=0) -> list:
        """
        Creates a fingerprint matrix (heatmap) on the format expected by the
        fingerprinting algorithms. Fetched from our database and
        converted to the correct data structure.
        """
        fingerprint = self.get_fingerprint(fingerprint_id)
        heatmap = []
        for i in self.numbers:
            row = []
            for letter in self.letters:
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

    def get_all_heatmaps(self, locator_ids):
        """
        Fetches heatmaps for all locators from our database.
        """
        heatmaps = {}
        for locator_id in locator_ids:
            heatmaps[locator_id] = self.create_heatmap(locator_id)
        return heatmaps

    def create_random_fingerprint(self):
        """
        Creates a random heatmap/fingerprint from random values.
        """
        fingerprint = {}
        locator_ids = np.array([8, 12, 7, 10, 11, 9])
        for char in self.numbers:
            for i in self.letters:
                square_name = chr(char) + str(i)
                fingerprint[square_name] = {}
                locators = np.random.choice(
                    locator_ids, random.randint(1,
                                                len(locator_ids) - 1))
                for locator in locators:
                    fingerprint[square_name][str(locator)] = random.randint(
                        -100, -20)

        self.db_client.testdb.fingerprint.insert_one(fingerprint)
