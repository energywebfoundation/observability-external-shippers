
from hexbytes import HexBytes
import json


class HexJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, HexBytes):

            return obj.hex()

        return super().default(obj)
