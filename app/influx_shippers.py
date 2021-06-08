
import influxdb_client
import json
from influxdb_client.client.write_api import SYNCHRONOUS
from HexJsonEncoder import HexJsonEncoder

#Const.
HTTP_CODE_ERROR = 500
HTTP_CODE_BAD_REQUEST = 401
HTTP_CODE_OK = 200


def data_prepare_influx(influx_payload):

    #influx data structure
    influx_dict_structure = {
        "measurement":"authorOfBlock",
        "fields": influx_payload
    }

    #print structure
    structure_to_print = json.dumps(influx_dict_structure,cls=HexJsonEncoder)

    return influx_dict_structure, structure_to_print


def send_to_influx(influx_payload, influx_url, influx_bucket_id, influx_token, influx_org):
    
    client = influxdb_client.InfluxDBClient(
        url=influx_url,
        token=influx_token,
        org=influx_org
    )

    write_api = client.write_api(
        write_options=SYNCHRONOUS
    )
    try:
        write_api.write(bucket=influx_bucket_id, record=influx_payload)
        text = "Data send"
        status_code = HTTP_CODE_OK
    except Exception as e:
        text = str(e)
        status_code = HTTP_CODE_ERROR

    #clossing connections
    write_api.close()
    client.close()

    return text, status_code
