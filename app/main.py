from flask import Flask
from web3 import Web3
import json
from hexbytes import HexBytes

web3 = Web3(Web3.HTTPProvider("http://3.235.186.90:80"))
app = Flask(__name__)

class HexJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, HexBytes):
            return obj.hex()
        return super().default(obj)

@app.route('/')
def hello():
    return "Hello from Observability Pipeline!"


@app.route('/block/<int:number>')
def block(number):
    block = web3.eth.getBlock(number)
    block_dict = dict(block)

    block_json = json.dumps(block_dict,cls=HexJsonEncoder)

    # result = print(block_json)

    return "Result is " + block_json

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')


