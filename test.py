import requests

# this is the base url, location of the api
BASE = "http://127.0.0.1:5000/"

response = requests.put(BASE + "BeaconValue/2",
                        {"id": "hisdnw", "imei": 6, "lastActive": "19-128-12_7"})
print(response.json())
response = requests.put(BASE + "BeaconValue/3",
                        {"id": "j8ei", "imei": 9, "lastActive": "19-13d28-12_7"})
print(response.json())
response = requests.put(BASE + "BeaconValue/6",
                        {"id": "j8ei", "imei": 9, "lastActive": "19-13d28-12_7"})
print(response.json())
# input()
response = requests.get(BASE + "BeaconValue/6")
print(response.json())

response = requests.delete(BASE + "BeaconValue/6")
print(response)

response = requests.get(BASE + "BeaconValue/6")
print(response.json())
