"""Norbit"""

import requests
import json
import datetime

from env import *
from requests.models import Response


class NorbitApi():
    def __init__(self):
        self.api_url = API_URL
        self.headers = {
            "X-API-KEY": API_KEY,
            "X-API-SECRET": API_SECRET,
        }

    def get_companies(self):
        """
        Returns information about all companies
        """
        request_url = self.api_url + f"companies"
        return requests.get(request_url, headers=self.headers)

    def get_company(self, company_id: int):
        """
        Returns information about a company given company id
        """
        request_url = self.api_url + f"company/{company_id}"
        return requests.get(request_url, headers=self.headers)

    def get_gateways(self, company_id: int):
        """
        Returns information about all gateways 
        linked to a specific company
        E.g. company_id = 1 (Norbit)
        """
        request_url = self.api_url + f"gateways/{company_id}"
        return requests.get(request_url, headers=self.headers)

    def get_gateway(self, gateway_id: int):
        """
        Returns information about a single gateway with a
        specific gateway id.
        E.g. gateway_id = 1
        """
        request_url = self.api_url + \
            f"gateway/{gateway_id}"
        return requests.get(request_url, headers=self.headers)

    def get_devices(self, device_type: str, company_id=None):
        """
        Returns information about all devices with a specific device type
        (and company id if specified).
        E.g. device_type = "locator", company_id = 1 (Norbit)
        """
        company_id_url = ""
        if company_id is not None:
            company_id_url = f"/{company_id_url}"
        request_url = self.api_url + f"devices{company_id_url}/{device_type}"
        return requests.get(request_url, headers=self.headers)

    def get_device(self, company_id: int, device_id: int, device_type: str):
        """
        Returns information about a single device with a
        specific device id and device type.
        E.g. company_id = 1 (Norbit), device_id = 1, device_type = "locator"
        """
        request_url = self.api_url + \
            f"device/{company_id}/{device_id}/{device_type}"
        return requests.get(request_url, headers=self.headers)

    def get_td_by_limit(self, company_id: int, device_id: int, gateway_id: int,
                        limit: int):
        """
        Returns the last 'limit' TDs given company, device, gateway and limit.
        limit: number of 'pings' to return
        """
        request_url = self.api_url + \
            f"td/device/{company_id}/{device_id}/{gateway_id}/{limit}"
        return requests.get(request_url, headers=self.headers)

    def get_td_by_device(self, company_id: int, device_id: int,
                         last_hours: int):
        """
        Returns the last TDs from specific device given company, 
        device and last hours.
        last_hours: int, returns all pings during the given last hours
        """
        request_url = self.api_url + \
            f"td/device/{company_id}/{device_id}/{last_hours}"
        return requests.get(request_url, headers=self.headers)

    def get_td_by_gateway(self, company_id: int, gateway_id: int,
                          last_hours: int):
        """
        Returns the last TDs from specific device given company, 
        gateway and last hours.
        last_hours: int, returns all pings during the given last hours
        """
        request_url = self.api_url + \
            f"td/device/{company_id}/{gateway_id}/{last_hours}"
        return requests.get(request_url, headers=self.headers)

    def get_td_by_time_interval(self, company_id: int, device_id: int,
                                dateTimeFrom: int, dateTimeTo: int):
        """
        Returns the TDs from specific device given company, 
        gateway and time interval.
        dateTimeFrom: start time of time interval
        dateTimeTo: end time of time interval
        """
        request_url = self.api_url + \
            f"td/device/{company_id}/{device_id}/period/{dateTimeFrom}/{dateTimeTo}"
        return requests.get(request_url, headers=self.headers)


def get_time_stamp_format(year: int,
                          month: int,
                          day: int,
                          hour=0,
                          minute=0,
                          second=0):
    """
    Returns a timestamp on the format requiered by the api.
    """
    return datetime.datetime(year, month, day, hour, minute,
                             second).strftime("%Y-%m-%dT%H:%M:%S.%f")


def json_to_text(json_obj: list):
    """
    Returns a printable user-friendly representation of the given json-object.
    """
    return json.dumps(json_obj, sort_keys=True, indent=4)


def print_response(response: requests.models.Response):
    """
    Prints the api response in a user-friendly way.
    """
    print("Status code:", response.status_code)
    json_response = response.json()
    print(json_to_text(json_response))


if __name__ == "__main__":
    api = NorbitApi()

    # response = api.get_companies()
    # response = api.get_company(company_id=1)

    # response = api.get_gateways(company_id=1)

    # response = api.get_devices("locator")
    # # Denne virker ikke, antar get_gateways brukes i stedet.

    # response = api.get_devices("smart_tag")

    # response = api.get_device(company_id=1,
    #                                  device_id=5,
    #                                  device_type="smart_tag")

    # response = api.get_td_by_limit(company_id=1,
    #                                   device_id=1,
    #                                   gateway_id=1,
    #                                   limit=2)

    # response = api.get_td_by_device(company_id=1,
    #                                    device_id=5,
    #                                    last_hours=1000)

    # response = api.get_td_by_gateway(company_id=1,
    #                                  gateway_id=1,
    #                                  last_hours=3000)

    # print_response(response)

    start = get_time_stamp_format(2021, 5, 27)
    stop = get_time_stamp_format(2021, 5, 28)
    response = api.get_td_by_time_interval(company_id=1,
                                           device_id=1,
                                           dateTimeFrom=start,
                                           dateTimeTo=stop)

    print_response(response)
