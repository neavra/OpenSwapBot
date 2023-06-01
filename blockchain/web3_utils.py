from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()
NODE_PROVIDER_ENDPOINT = os.getenv("NODE_PROVIDER_ENDPOINT")

# Function to retrieve Ethereum data
def get_ethereum_data():
    # Create a web3 instance using the Infura endpoint
    web3 = Web3(Web3.HTTPProvider(NODE_PROVIDER_ENDPOINT))

    # Get the current gas price
    gas_price = web3.eth.gas_price

    # Get the latest block number
    block_number = web3.eth.block_number

    # Convert gas price to gwei
    gas_fee = round(web3.from_wei(gas_price, 'gwei'), 1)
    return gas_fee, block_number
