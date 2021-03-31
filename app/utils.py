import json
from hexbytes import HexBytes
import time
import influxdb_client
import numpy
from scipy import stats
from influxdb_client.client.write_api import SYNCHRONOUS


class HexJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, HexBytes):
            return obj.hex()
        return super().default(obj)

def get_last_block(web3):
    block_number = 1
    try:
        block = web3.eth.get_block('latest')
        text = "Got the latest block"
        status_code = 200
        block_number = block['number']
    except Exception as e:
        text = str(e)
        status_code = "888"
        return text, status_code, 
    
    return text, status_code, block_number
    
def get_data(number, web3):

    submission = {}
    try:
        block = web3.eth.getBlock(number)
        text = "All ok!"
        status_code = 200
    except Exception as e:
        text = str(e)
        status_code = "888"
        return text, status_code, submission
    
    submission["blockNumber"] = number
    submission["validator"]=block['miner']
    submission["blockHash"] = block['hash'].hex()
    submission["blockTimestamp"] = block['timestamp']
    submission["currentTimestamp"] = time.time()
    submission["timeSinceLastBlock"] = web3.eth.getBlock(number-1)['timestamp'] - submission["blockTimestamp"]
    submission["blockSize"] = block['size'] #Integer the size of this block in bytes.
    submission["blockGasUsed"] = block['gasUsed']


    #tx stats
    # 
    totalGasFee = 0 #gwei
    gasPriceList = []
    uniqueActors = set()
    submission["SuccessfulTx"] = 0 # receipt status 1
    submission["FailedTx"] = 0 # receipt status 0
    
    for transaction in block['transactions']:
        try:
            tx = web3.eth.getTransaction(transaction)
            receipt = web3.eth.waitForTransactionReceipt(transaction)
            text = "All ok!"
            status_code = 200

        except Exception as e:
            text = str(e)
            status_code = "888"
            return text, status_code, submission
            #example reverted 0x68d019917d9d3b1162899d2495413be5f70e7fbd2175157062d0c1f4115465ef 
            #example successful 
            # 
        if receipt['status'] == 1:
            submission["SuccessfulTx"] += 1
        else:
            submission["FailedTx"] += 1

        totalGasFee += tx['gasPrice']*receipt['gasUsed'] #gas price * gas used = gas payed
        #Check this line
        gasPriceList.append(tx['gasPrice'])
        uniqueActors.add(tx['from'])
        uniqueActors.add(tx['to'])
        
    submission["TxCount"] = len(block['transactions'])
    submission["TxUniqueActors"] = len(uniqueActors)
    if gasPriceList:
        submission["TxGasPriceMin"] = min(gasPriceList)
        submission["TxGasPriceMax"] = max(gasPriceList)
        submission["TxGasPriceMean"] = numpy.mean(gasPriceList)
        submission["TxGasPriceWeightedMean"] = totalGasFee / block['gasUsed']
        submission["TxGasPriceSkew"] = stats.skew(gasPriceList)

    
    return text, status_code, submission


def get_all_transactions(number, rpc):
    submission = {}
    #get all transactions
    """curl --data '{"method":"parity_allTransactions","params":[],"id":1,"jsonrpc":"2.0"}' -H "Content-Type: application/json" -X POST localhost:8545"""

    parity_body = {
        "method":"parity_allTransactions",
        "params":[],
        "id":1,
        "jsonrpc":"2.0"
    }

    text, status_code = rpc.post(parity_body)
    if status_code != "888":
        
        result_dict_all_transactions = json.loads(text)["result"]

        if result_dict_all_transactions:
            PendingGasPriceList = [int(x['gasPrice'],16) for x in result_dict_all_transactions]  #prices are in wei
            submission["PendingTxCount"] = len(result_dict_all_transactions)
            submission["PendingTxGasPriceMin"] = min(PendingGasPriceList)
            submission["PendingTxGasPriceMax"] = max(PendingGasPriceList)
            submission["PendingTxGasPriceMean"] = numpy.mean(PendingGasPriceList)
            submission["PendingTxGasPriceSkew"] = stats.skew(PendingGasPriceList)

    return text, status_code, submission


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
        status_code = 200
    except Exception as e:
        text = str(e)
        status_code = 500

    #clossing connections
    write_api.close()
    client.close()

    return text, status_code
