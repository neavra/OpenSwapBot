from web3 import Web3
from eth_account import Account
import secrets
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

def create_wallet():
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    account = Account.from_key(private_key)
    public_key = account.address

    return public_key, private_key


def get_balance(public_key):
    # Connect to an Ethereum node using Web3
    web3 = Web3(Web3.HTTPProvider(NODE_PROVIDER_ENDPOINT))

    # Get the balance in Wei
    balance_wei = web3.eth.get_balance(public_key)

    # Convert the balance from Wei to ETH
    balance_eth = web3.from_wei(balance_wei, 'ether')

    return balance_eth

def get_nonce(public_key):
    # Connect to an Ethereum node using Web3
    web3 = Web3(Web3.HTTPProvider(NODE_PROVIDER_ENDPOINT))

    # Get the nonce
    nonce = web3.eth.get_transaction_count(public_key)

    return nonce
