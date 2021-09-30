from pydantic import BaseModel
import datetime
from fastapi.encoders import jsonable_encoder


class Gateways(BaseModel):
    _id: str
    awsThingName: str
    friendlyName: str
    imei: str
    lastActive: datetime
    positionLng: str
    positionLat: str

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)


class Location(BaseModel):
    id: str
    positionLng: str
    positionLat: str
    date: datetime

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)
