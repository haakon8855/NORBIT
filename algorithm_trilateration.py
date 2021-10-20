import pymongo
from pandas import DataFrame
import math
import numpy as np
import utm
from scipy.optimize import minimize

ALG_VER = "trilateration"


def algorithm_trilateration(db_client: pymongo.MongoClient):
    """
    Fetches telemetry data from the database, predicts location for each
    beacon, and stores the predicted locations in the database.
    """
    data = DataFrame(
        # db_client.testdb.callibrationData.find())
        # db_client.testdb.callibrationData.find({'timestamp': 1633680792}))
        # db_client.testdb.callibrationData.find({'timestamp': 1633673904}))
        db_client.testdb.callibrationData.find({'timestamp': 1633673758}))
    data = data[[
        "rssi", "gatewayId", "gatewayLat", "gatewayLng", "positionLat",
        "positionLng", "timestamp"
    ]]
    print(data)

    data = data.drop_duplicates(subset="gatewayId", keep="last")

    predicted_locations = []

    # For each deviceId:
    predicted_locations.append(prediction(data))
    print(predicted_locations)
    # db_client.testdb.estimatedPosition.insert_many(predictedLocations)


def prediction(data):
    """
    Calculates predicted location for all beacons with updates. Then stores
    the predicted locations in the database.
    """
    deviceId = 41
    if len(data) == 1:
        return {
            "deviceId": deviceId,
            "latitude": data["gatewayLat"],
            "longitude": data["gatewayLng"],
            "timestamp": data["timestamp"],
            "algorithm": "gateway_position"
        }
    elif len(data) == 2:
        # Set in middle, towards the one with best rssi
        data['dist'] = rssi2dist(data['rssi'])
        data = data.sort_values(by=['dist']).iloc[0:2, :]
        print(data)
        weight1 = data['dist'].iloc[0] / (data['dist'].iloc[0] +
                                          data['dist'].iloc[1])
        weight2 = data['dist'].iloc[1] / (data['dist'].iloc[0] +
                                          data['dist'].iloc[1])
        lat = data['gatewayLat'].iloc[0] * weight2 + data['gatewayLat'].iloc[
            1] * weight1
        lng = data['gatewayLng'].iloc[0] * weight2 + data['gatewayLng'].iloc[
            1] * weight1
        lat = (lat + data['gatewayLat'].mean()) / 2
        lng = (lng + data['gatewayLng'].mean()) / 2
        return {
            "deviceId": deviceId,
            "latitude": round(lat, 6),
            "longitude": round(lng, 6),
            "timestamp": int(data["timestamp"].mean()),
            "algorithm": "weighted_mean"
        }
    else:
        # rssi -> dist
        data["dist"] = rssi2dist(data["rssi"])
        data = data.sort_values(by="dist")
        print(data)

        distances_to_gateways = np.array(data["dist"])
        gateways = np.array(data[["gatewayLat", "gatewayLng"]])

        # pred_lat, pred_lng = trilat(distances_to_gateways, gateways)
        pred_lat, pred_lng = trilat(distances_to_gateways, gateways)
        if pred_lat is None or pred_lng is None:
            return prediction(data.iloc[0:2, :])
        return {
            "deviceId": deviceId,
            "latitude": round(pred_lat, 6),
            "longitude": round(pred_lng, 6),
            "timestamp": int(data["timestamp"].mean()),
            "algorithm": ALG_VER
        }


def rssi2dist(rssis):
    measured_power = -69  # Factory calibrated?
    N = 1.14  # Environmental factor
    return 10**((measured_power - rssis) / (10 * N))


def gps_solve(distances_to_station, stations_coordinates):
    def error(x, c, r):
        return sum([(np.linalg.norm(x - c[i]) - r[i])**2
                    for i in range(len(c))])

    l = len(stations_coordinates)
    S = sum(distances_to_station)
    # compute weight vector for initial guess
    W = [((l - 1) * S) / (S - w) for w in distances_to_station]
    # get initial guess of point location
    x0 = sum([W[i] * stations_coordinates[i] for i in range(l)])
    # optimize distance from signal origin to border of spheres
    return minimize(error,
                    x0,
                    args=(stations_coordinates, distances_to_station),
                    method='Nelder-Mead').x


def trilat(distances_to_gateways, gateways):
    xA, yA, colA, rowA = utm.from_latlon(float(gateways[0][0]),
                                         float(gateways[0][1]))
    xB, yB, colB, rowB = utm.from_latlon(float(gateways[1][0]),
                                         float(gateways[1][1]))
    xC, yC, colC, rowC = utm.from_latlon(float(gateways[2][0]),
                                         float(gateways[2][1]))

    stations = list(np.array([[xA, yA], [xB, yB], [xC, yC]]))
    solution = gps_solve(distances_to_gateways, stations)
    print(solution)

    return utm.to_latlon(solution[0], solution[1], colA, rowA)
