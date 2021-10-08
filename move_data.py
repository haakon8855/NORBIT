import pymongo
from norbit_api import *

if __name__ == "__main__":
    api = NorbitApi()
    response = api.get_td_by_device(1, 41, 2)
    client = pymongo.MongoClient(DB_URI, port=DB_PORT, tls=True, tlsAllowInvalidHostnames=True,
                             tlsCAFile=DB_CA_FILE, username=DB_USERNAME, password=DB_PASSWORD)
    db = client.testdb
    db.callibrationData.insert_many(response.json())
    client.close()