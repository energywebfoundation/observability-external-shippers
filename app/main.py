from flask import Flask, request, jsonify
from web3 import Web3
from threading import Thread
import time
import logging
import os

from influx_shippers import send_to_influx
from influx_shippers import data_prepare_influx
from blockchain_data import get_data
from blockchain_data import get_all_transactions
from blockchain_data import get_last_block
from Http_requests import Http_requests


#add dynamodb or alternative storage - tfe user additional policy attachment
#add secretstore
#add elastic shipper
#add cloudwatch shipper
#add k8s deployment

#general variables
app = Flask(__name__)
rpc_url = os.environ["rpc_url"]
auth_key = os.environ["auth_key"]

#Get block class
web3 = Web3(Web3.HTTPProvider(rpc_url))

#parity allTransactions
parity_headers = {
    "Content-Type":"application/json"
}

rpc = Http_requests(url=rpc_url, token="notoken",authorization="noauth",headers=parity_headers)

#Feature toggle
stop_run = False
log_level = os.environ["log_level"]

logger = logging.getLogger()
logger.setLevel(log_level)

#Const.
HTTP_CODE_ERROR = 500
HTTP_CODE_BAD_REQUEST = 401
HTTP_CODE_OK = 200

# Variables influx
influx_url = os.environ["influx_url"]
influx_bucket_id = os.environ["influx_bucket_id"]
influx_token = os.environ["influx_token"]
influx_org = os.environ["influx_org"]

def iteration_start(number):
    global stop_run
    number = number
    retry_int = 0
    
    while not stop_run:

        #payload get
        app.logger.info("TransactionID is " +str(number) +  " Currently: getting last block number")
        text_check_last_block, status_code_last_block, block_number = get_last_block(web3)
        app.logger.info("TransactionID is " +str(number) +  " Last block is " + str(block_number))

        if block_number < number:
            number = block_number
            time.sleep(4)
            continue

        app.logger.info("TransactionID is " +str(number) +  " Currently: getting data from the block")
        text_block, status_code_block, payload_block = get_data(number, web3)

        app.logger.info("TransactionID is " +str(number) +  " Currently: getting all transactions from the block")
        text_all_transactions, status_code_transactions, payload_transactions = get_all_transactions(number, rpc)

        payload = payload_block | payload_transactions

        app.logger.info("TransactionID is " +str(number) +  " Payload for influx is: " + str(payload))

        #prepare Influx data structures
        app.logger.info("TransactionID is " +str(number) +  " Currently: sending payload to be prepared for influx")
        influx_dict_structure, structure_to_print = data_prepare_influx(payload)

        app.logger.info("TransactionID is " +str(number) +  " Influx payload prepared is: " + str(influx_dict_structure))
        #Send to influx
        app.logger.info("TransactionID is " +str(number) +  " Currently: sending prepared paylod to influx")
        result_of_send, status_code = send_to_influx(influx_dict_structure, influx_url, influx_bucket_id, influx_token, influx_org)
        app.logger.info("TransactionID is " +str(number) +  " Result of sending to influx is " + str(result_of_send))

        if status_code == HTTP_CODE_ERROR:
            retry_int+=1
        else:
            retry_int = 0
            number+=1
            
        if retry_int >= 5:
            break
        app.logger.info("TransactionID is " +str(number) +  " Currently - finishing iteration " + str(number))
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



### ROUTES ###


@app.route("/stop", methods=['POST'])
def stop():

    #authorization
    headers = request.headers
    auth = headers.get("X-Api-Key")
    if auth != auth_key:
        return jsonify({"message": "ERROR: Unauthorized"}), HTTP_CODE_BAD_REQUEST

    global stop_run
    stop_run = True
    return jsonify({"message": "OK: Authorized, application stopped"}), HTTP_CODE_OK

@app.route("/run/<int:number>", methods=['POST'])
def run(number):

    #authorization
    headers = request.headers
    auth = headers.get("X-Api-Key")
    if auth != auth_key:
        return jsonify({"message": "ERROR: Unauthorized"}), HTTP_CODE_BAD_REQUEST

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
        return jsonify({"message": "ERROR: Unauthorized"}), HTTP_CODE_BAD_REQUEST

    result_of_send, status_code, structure_to_print = single_request_worker(number)
    

    return "Result is " + structure_to_print

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')


