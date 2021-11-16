"""
move_data is used to move data from NORBIT's database
to our database using their API.
"""
import datetime as dt
import pymongo
from requests.models import Response

from data_processing.norbit_api import NorbitApi


class MoveData():
    """
    Move data can move data from NORBIT's API to our database
    """
    def __init__(self, db_client: pymongo.MongoClient):
        self.db_client = db_client

    @staticmethod
    def convert_timestamp(tds: Response) -> list:
        """
        Converts the timestamp used by NORBIT on the format
        "YYYY-mm-ddTHH:MM:SS.xxxx" to standard unicode timestamp.
        """
        tds = tds.json()
        for index, telem_data in enumerate(tds):
            timestamp = telem_data["timestamp"]
            timestamp = dt.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
            telem_data["timestamp"] = int(timestamp.timestamp())
            tds[index] = telem_data
        return tds

    def get_last_updated(self, collection: str) -> int:
        """
        Returns all telemetry data from NORBIT's API not stored in our database.
        """
        data = self.db_client.testdb[collection].find({}, {
            "_id": 0,
            "timestamp": 1
        })
        return max(map(lambda td: td["timestamp"], data))

    def update_calibration(self, company_id: int, device_id: int,
                           last_updated: int) -> int:
        """
        Fetches calibration packets from NORBIT's API, given it's device_id.
        """
        api = NorbitApi()
        data = api.get_td_by_device(company_id, device_id, 300)

        if len(data.json()) == 0:
            return 0

        tds = MoveData.convert_timestamp(data)
        tds_filtered = list(
            filter(lambda td: td["timestamp"] > last_updated, tds))

        if len(tds_filtered) == 0:
            return 0

        self.db_client.testdb["callibrationData"].insert_many(tds_filtered)
        return max(map(lambda td: td["timestamp"], tds_filtered))
