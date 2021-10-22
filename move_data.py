import pymongo
import datetime as dt
from requests.models import Response

from norbit_api import NorbitApi
from env import *


def convert_timestamp(tds: Response) -> list[dict]:
    tds = tds.json()
    for index, td in enumerate(tds):
        timestamp = td["timestamp"]
        timestamp = dt.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        td["timestamp"] = int(timestamp.timestamp())
        tds[index] = td

    return tds


def get_last_updated(db_client: pymongo.MongoClient, collection: str) -> int:
    data = db_client.testdb[collection].find({}, {"_id": 0, "timestamp": 1})
    return max(map(lambda td: td["timestamp"], data))


def update_callibration(db_client: pymongo.MongoClient, company_id: int,
                        device_id: int, last_updated: int) -> int:
    api = NorbitApi()
    data = api.get_td_by_device(company_id, device_id, 300)

    if len(data.json()) == 0:
        return 0

    tds = convert_timestamp(data)
    tds_filtered = list(filter(lambda td: td["timestamp"] > last_updated, tds))

    if len(tds_filtered) == 0:
        return 0

    db_client.testdb["callibrationData"].insert_many(tds_filtered)
    return max(map(lambda td: td["timestamp"], tds_filtered))


if __name__ == "__main__":
    pass