import requests

# this is the base url, location of the api
BASE = "http://127.0.0.1:5000/"

response = requests.post(BASE + "td/2", json=
                        {
                            "_id": 2,
                            "timestamp": "2021-09-30T08:39:56.846Z",
                            "deviceId": 1,
                            "gatewayId": 1,
                            "positionLat": 63.443434,
                            "positionLng": 10.429496,
                            "positionAlt": 3,
                            "positionHdop": 0,
                            "rssi": -34,
                            "created": "2021-09-30T08:39:56.846Z",
                            "gatewayLat": 63.443434,
                            "gatewayLng": 10.429496,
                            "gatewayAlt": 2,
                        })
print(response)
response = requests.post(BASE + "td/3", json=
                        {
                            "_id": 3,
                            "timestamp": "2021-09-30T08:39:56.846Z",
                            "deviceId": 1,
                            "gatewayId": 1,
                            "positionLat": 63.443434,
                            "positionLng": 10.429496,
                            "positionAlt": 3,
                            "positionHdop": 0,
                            "rssi": -34,
                            "created": "2021-09-30T08:39:56.846Z",
                            "gatewayLat": 63.443434,
                            "gatewayLng": 10.429496,
                            "gatewayAlt": 2,
                        })
print(response)
response = requests.post(BASE + "td/6", json=
                        {
                            "_id": 6,
                            "timestamp": "2021-09-30T08:39:56.846Z",
                            "deviceId": 1,
                            "gatewayId": 1,
                            "positionLat": 63.443434,
                            "positionLng": 10.429496,
                            "positionAlt": 3,
                            "positionHdop": 0,
                            "rssi": -34,
                            "created": "2021-09-30T08:39:56.846Z",
                            "gatewayLat": 63.443434,
                            "gatewayLng": 10.429496,
                            "gatewayAlt": 2,
                        })
print(response)
# input()
response = requests.get(BASE + "td/6")
print(response)

response = requests.delete(BASE + "td/6")
print(response)

response = requests.get(BASE + "td/6")
print(response)
