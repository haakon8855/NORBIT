from pymongo import MongoClient
from pprint import pprint
import datetime
# connect to MongoDB, change the << MONGODB URL >> to reflect your own connection string
# Username and password for cloud:
#Username: NORBIT
# PasswordOFNvXhOKBipn9ieq
client = MongoClient(
    "mongodb+srv://NORBIT:OFNvXhOKBipn9ieq@cluster0.nc1za.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

# # Create collection (collection = Table)
# db = client.gettingStarted
# # create row
# test = db.test

# # JSON formatted for input row
# testDocument = {
#     "name": {"First": "NORBIT", "Last": "Kundestyrt"}
# }
# # Insert row
# test.insert_one(testDocument)

# # Issue the serverStatus command and print the results
# serverStatusResult = db.command("serverStatus")
