"""
algorithm_multilateration provides location estimation using multilateration
"""
from pandas import DataFrame
from scipy.optimize import minimize
import numpy as np
import pymongo
import utm


def algorithm_multilateration(db_client: pymongo.MongoClient,
                              test_accuracy: bool = False):
    """
    Fetches telemetry data from the database, predicts location for each
    beacon, and stores the predicted locations in the database.
    """
    data_filter = [
        "rssi", "gatewayId", "gatewayLat", "gatewayLng", "positionLat",
        "positionLng", "timestamp"
    ]

    timestamps_test_set = [1633680792, 1633673904, 1633673758]
    if test_accuracy:
        predicted_locations = []
        for i, timestamp in enumerate(timestamps_test_set):
            data = DataFrame(
                db_client.testdb.callibrationData.find(
                    {'timestamp': timestamp}))
            data = data[data_filter]
            data = data.drop_duplicates(subset="gatewayId", keep="last")
            predicted_locations.append(prediction(data))

            true_loc = np.array([
                round(data['positionLat'].iloc[i], 5),
                round(data['positionLng'].iloc[i], 5)
            ])
            pred_loc = np.array([
                round(predicted_locations[i]['latitude'], 5),
                round(predicted_locations[i]['longitude'], 5)
            ])

            accuracy = round(haversine(true_loc, pred_loc), 1)
            print(f'Timestamp: {timestamp}s', f'\nAccuracy: {accuracy}m',
                  f'\nTrue loc: {true_loc}', f'\nPred loc: {pred_loc}\n')
        # db_client.testdb.calibrationEstimatedPosition.insert_many(predicted_locations)
        return

    data = DataFrame(db_client.testdb.callibrationData.find())

    data = data[data_filter]
    data = data.sort_values(by=['timestamp'])
    data = data.drop_duplicates(subset="gatewayId", keep="last")

    predicted_locations = []

    # For each device_id:
    predicted_locations.append(prediction(data))
    # db_client.testdb.calibrationEstimatedPosition.insert_many(predictedLocations)


def prediction(data):
    """
    Calculates predicted location for all beacons with updates. Then stores
    the predicted locations in the database.
    """
    device_id = 41
    if len(data) == 1:
        return {
            "deviceId": device_id,
            "latitude": data["gatewayLat"],
            "longitude": data["gatewayLng"],
            "true_latitude": data["positionLat"].iloc[0],
            "true_longitude": data["positionLng"].iloc[0],
            "timestamp": data["timestamp"],
            "algorithm": "gateway_position"
        }
    elif len(data) == 2:
        # Set in middle, towards the one with best rssi
        data['dist'] = rssi_to_dist(data['rssi'])
        data = data.sort_values(by=['dist']).iloc[0:2, :]
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
            "deviceId": device_id,
            "latitude": round(lat, 6),
            "longitude": round(lng, 6),
            "true_latitude": data["positionLat"].iloc[0],
            "true_longitude": data["positionLng"].iloc[0],
            "timestamp": int(data["timestamp"].mean()),
            "algorithm": "weighted_mean"
        }
    else:
        # rssi -> dist
        data["dist"] = rssi_to_dist(data["rssi"])
        data = data.sort_values(by="dist")

        gateways = np.array(data[["gatewayLat", "gatewayLng"]])
        distances_to_gateways = np.array(data["dist"])

        # Filter out gateways which are too far away to increase accuracy
        filtered_data = data[data['dist'] < 50]
        if len(filtered_data) > 2:
            gateways = np.array(filtered_data[["gatewayLat", "gatewayLng"]])
            distances_to_gateways = np.array(filtered_data["dist"])

        try:
            # Estimate position using multilateration
            pred_lat, pred_lng = multilateration(distances_to_gateways,
                                                 gateways)
        except (AttributeError, ValueError):
            # If something fails, fall back to weighted_mean-method
            return prediction(data.iloc[0:2, :])
        return {
            "deviceId": device_id,
            "latitude": round(pred_lat, 6),
            "longitude": round(pred_lng, 6),
            "true_latitude": data["positionLat"].iloc[0],
            "true_longitude": data["positionLng"].iloc[0],
            "timestamp": int(data["timestamp"].mean()),
            "algorithm": "trilateration"
        }


def rssi_to_dist(rssi):
    """
    Calculates an estimated distance between beacon and locator based on
    measured rssi at locator.
    """
    measured_power = -69  # Factory calibrated?
    N = 1.14  # Environmental factor
    return 10**((measured_power - rssi) / (10 * N))


def multilateration(distances_to_gateways, gateways):
    """
    Converts latitude/longitude coordinates to UTM-coordinates and returns
    the best-fit location of a beacon using multilateration.
    """
    stations = []

    # Default utm square in southern Norway
    col = 32
    row = 'V'

    for gateway in gateways:
        x_coord, y_coord, col, row = utm.from_latlon(gateway[0], gateway[1])
        stations.append([x_coord, y_coord])

    stations = list(np.array(stations))
    solution = gps_solve(distances_to_gateways, stations)

    return utm.to_latlon(solution[0], solution[1], col, row)


def gps_solve(distances_to_station, stations_coordinates):
    """
    Finds the best-fit location of a beacon given a list of coordinates to
    locators in 2d-space and the distance to them.
    """
    def error(x, c, r):
        return sum([(np.linalg.norm(x - c[i]) - r[i])**2
                    for i in range(len(c))])

    length = len(stations_coordinates)
    total = sum(distances_to_station)
    # compute weight vector for initial guess
    weight = [((length - 1) * total) / (total - w)
              for w in distances_to_station]
    # get initial guess of point location
    x_0 = sum([weight[i] * stations_coordinates[i] for i in range(length)])
    # optimize distance from signal origin to border of spheres
    return minimize(error,
                    x_0,
                    args=(stations_coordinates, distances_to_station),
                    method='Nelder-Mead').x


def haversine(loc1, loc2, radius=6371e3):
    """
    Calculates distance between loc1 and loc2. Both must be latitude/longitude
    coordinates representing two positions on the earth's surface.
    """
    phi_1 = loc1.T[0] * np.pi / 180
    phi_2 = loc2.T[0] * np.pi / 180
    delta_phi = (loc2.T[0] - loc1.T[0]) * np.pi / 180
    delta_lambda = (loc2.T[1] - loc1.T[1]) * np.pi / 180
    alpha = np.sin(delta_phi / 2)**2 + np.cos(phi_1) * np.cos(phi_2) * np.sin(
        delta_lambda / 2)**2
    chi = 2 * np.arctan2(np.sqrt(alpha), np.sqrt(1 - alpha))
    return radius * chi
