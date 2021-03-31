from flask import Flask, request, jsonify
from web3 import Web3
from threading import Thread
import time
import logging
from utils import send_to_influx
from utils import data_prepare_influx
from utils import get_data
from utils import get_all_transactions
from utils import get_last_block
from Service import Resource


#add dynamodb or alternative storage - tfe user additional policy attachment
#add secretstore
#add elastic shipper
#add cloudwatch shipper
#add k8s deployment

#general variables
app = Flask(__name__)
rpc_url = "http://3.235.186.90:80"
auth_key = "asoidewfoef"

#Get block class
web3 = Web3(Web3.HTTPProvider(rpc_url))

#parity allTransactions
parity_headers = {
    "Content-Type":"application/json"
}

rpc = Resource(url=rpc_url, token="notoken",authorization="noauth",headers=parity_headers)

#Feature toggle
stop_run = False
log_level = "INFO"

logger = logging.getLogger()
logger.setLevel(log_level)

#logging.basicConfig(level=LOGGING_LEVEL)

# Variables influx
influx_url = "http://18.197.54.173:8086"
influx_bucket_id = "eww_buckett"
influx_token = ""
influx_org = "eww_organization"

def iteration_start(number):
    global stop_run
    number = number
    retry_int = 0
    
    while not stop_run:

        #payload get
        text_check_last_block, status_code_last_block, block_number = get_last_block(web3)
        app.logger.info("Last block is " + str(block_number))

        if block_number < number:
            number = block_number

        text_block, status_code_block, payload_block = get_data(number, web3)
        text_all_transactions, status_code_transactions, payload_transactions = get_all_transactions(number, rpc)

        payload = payload_block | payload_transactions

        app.logger.info("Payload is: " + str(payload))

        #prepare Influx data structures
        influx_dict_structure, structure_to_print = data_prepare_influx(payload)

        app.logger.info("Influx payload: " + str(influx_dict_structure))
        #Send to influx
        result_of_send, status_code = send_to_influx(influx_dict_structure, influx_url, influx_bucket_id, influx_token, influx_org)

        if status_code == 500:
            number = number
            retry_int+=1
        else:
            retry_int = 0
            number+=1
            
        if retry_int >= 5:
            break
        app.logger.info("Currently - block number is " + str(number))
        #time.sleep(1)
        print("running...")
    return result_of_send, status_code, structure_to_print

def single_request_worker(number):

    #payload get
    text_block, status_code_block, payload_block = get_data(number, web3)
    text_all_transactions, status_code_transactions, payload_transactions = get_all_transactions(number, rpc)

    payload = payload_block | payload_transactions

    #prepare Influx data structures
    influx_dict_structure, structure_to_print = data_prepare_influx(payload)
    #Send to influx
    result_of_send, status_code = send_to_influx(influx_dict_structure, influx_url, influx_bucket_id, influx_token, influx_org)

    return result_of_send, status_code, structure_to_print

def manual_run(number):
    t = Thread(target=iteration_start(number))
    t.start()
    return "Processing"

@app.route("/stop", methods=['POST'])
def stop():

    #authorization
    headers = request.headers
    auth = headers.get("X-Api-Key")
    if auth != auth_key:
        return jsonify({"message": "ERROR: Unauthorized"}), 401

    global stop_run
    stop_run = True
    return jsonify({"message": "OK: Authorized, application stopped"}), 200

@app.route("/run/<int:number>", methods=['POST'])
def run(number):

    #authorization
    headers = request.headers
    auth = headers.get("X-Api-Key")
    if auth != auth_key:
        return jsonify({"message": "ERROR: Unauthorized"}), 401

    global stop_run
    stop_run = False
    return manual_run(number)

@app.route('/')
def hello():
    return "Hello from Observability Pipeline!"

@app.route('/single_request/<int:number>',methods=['POST'])
def single_request(number):

    #authorization
    headers = request.headers
    auth = headers.get("X-Api-Key")
    if auth != auth_key:
        return jsonify({"message": "ERROR: Unauthorized"}), 401

    result_of_send, status_code, structure_to_print = single_request_worker(number)
    

    return "Result is " + structure_to_print

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')


