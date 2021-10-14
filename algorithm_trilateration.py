import pymongo
from pandas import DataFrame
import math
import numpy as np

ALG_VER = "trilateration"


def algorithm_trilateration(db_client: pymongo.MongoClient):
    """
    Calculates predicted location for all beacons with updates. Then stores
    the predicted locations in the database.
    """
    data = DataFrame(
        db_client.testdb.callibrationData.find({'timestamp': 1633673758}))
    # {'timestamp': {
    #     '$gt': 1633573592
    # }})
    data = data[[
        "rssi", "gatewayId", "gatewayLat", "gatewayLng", "positionLat",
        "positionLng", "timestamp"
    ]]

    predictedLocations = []

    # For each deviceId:
    deviceId = 41
    data = data.drop_duplicates(subset="gatewayId", keep="last")
    if len(data) == 1:
        predictedLocations.append({
            "deviceId": deviceId,
            "latitude": data["gatewayLat"],
            "longitude": data["gatewayLng"],
            "timestamp": data["timestamp"],
            "algorithm": ALG_VER
        })
    elif len(data) == 2:
        # Set in middle, towards the one with best rssi
        data.sort_values(by=["rssi"])
        # data["dist"] = rssi2dist(data["rssi"])
        # weight1 = data[0]["dist"] / (data[0]["dist"] + data[1]["dist"])
        # weight2 = data[1]["dist"] / (data[0]["dist"] + data[1]["dist"])
        predictedLocations.append({
            "deviceId":
            deviceId,
            "latitude":
            round(data["gatewayLat"].mean(), 6),
            "longitude":
            round(data["gatewayLng"].mean(), 6),
            "timestamp":
            int(data["timestamp"].mean()),
            "algorithm":
            ALG_VER
        })
    else:
        # rssi -> dist
        data["dist"] = rssi2dist(data["rssi"])
        data = data.sort_values(by="dist")

        distances_to_gateways = np.array(data["dist"])
        gateways = np.array(data[["gatewayLat", "gatewayLng"]])

        pred_lat, pred_long = trilat(distances_to_gateways, gateways)
        predictedLocations.append({
            "deviceId": deviceId,
            "latitude": round(pred_lat, 6),
            "longitude": round(pred_long, 6),
            "timestamp": int(data["timestamp"].mean()),
            "algorithm": ALG_VER
        })

    print(predictedLocations)
    # db_client.testdb.estimatedPosition.insert_many(predictedLocations)


def rssi2dist(rssis):
    measured_power = -69  # Factory calibrated?
    N = 1.14  # Environmental factor
    return 10**((measured_power - rssis) / (10 * N))


def trilat(distances_to_gateways, gateways):
    """
    Takes as an argument a line from the input file (see script docstring for
    expected format) and returns the trilaterated GPS coordinates of the
    sample.
    """
    earthR = 6371
    DistA = float(distances_to_gateways[0]) / 1000
    DistB = float(distances_to_gateways[1]) / 1000
    DistC = float(distances_to_gateways[2]) / 1000
    LatA = float(gateways[0][0])
    LonA = float(gateways[0][1])
    LatB = float(gateways[1][0])
    LonB = float(gateways[1][1])
    LatC = float(gateways[2][0])
    LonC = float(gateways[2][1])

    #   1. Convert Lat/Long to radians
    #   2. Convert Lat/Long(radians) to ECEF
    xA = earthR * (math.cos(math.radians(LatA)) * math.cos(math.radians(LonA)))
    yA = earthR * (math.cos(math.radians(LatA)) * math.sin(math.radians(LonA)))
    zA = earthR * (math.sin(math.radians(LatA)))

    xB = earthR * (math.cos(math.radians(LatB)) * math.cos(math.radians(LonB)))
    yB = earthR * (math.cos(math.radians(LatB)) * math.sin(math.radians(LonB)))
    zB = earthR * (math.sin(math.radians(LatB)))

    xC = earthR * (math.cos(math.radians(LatC)) * math.cos(math.radians(LonC)))
    yC = earthR * (math.cos(math.radians(LatC)) * math.sin(math.radians(LonC)))
    zC = earthR * (math.sin(math.radians(LatC)))

    P1 = np.array([xA, yA, zA])
    P2 = np.array([xB, yB, zB])
    P3 = np.array([xC, yC, zC])

    ex = (P2 - P1) / (np.linalg.norm(P2 - P1))
    i = np.dot(ex, P3 - P1)
    ey = (P3 - P1 - i * ex) / (np.linalg.norm(P3 - P1 - i * ex))
    ez = np.cross(ex, ey)
    d = np.linalg.norm(P2 - P1)
    j = np.dot(ey, P3 - P1)

    x = (pow(DistA, 2) - pow(DistB, 2) + pow(d, 2)) / (2 * d)
    y = ((pow(DistA, 2) - pow(DistC, 2) + pow(i, 2) + pow(j, 2)) /
         (2 * j)) - ((i / j) * x)

    z2 = pow(DistA, 2) - pow(x, 2) - pow(y, 2)
    if z2 < 0:
        z2 = 0
    z = np.sqrt(z2)

    #triPt is an array with ECEF x,y,z of trilateration point
    triPt = P1 + x * ex + y * ey + z * ez

    #convert back to lat/long from ECEF
    #convert to degrees
    lat = math.degrees(math.asin(triPt[2] / earthR))
    lon = math.degrees(math.atan2(triPt[1], triPt[0]))

    return lat, lon
