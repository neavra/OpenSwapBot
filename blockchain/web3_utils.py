from web3 import Web3
from eth_account import Account
import secrets
import os
import json
from dotenv import load_dotenv

load_dotenv()

NODE_PROVIDER_ENDPOINT = os.getenv("NODE_PROVIDER_ENDPOINT_TESTNET")
web3 = Web3(Web3.HTTPProvider(NODE_PROVIDER_ENDPOINT))

UNISWAP_ROUTER_ADDRESS = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6" # WETH Goerli


UNISWAP_ROUTER_ABI = [{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH9","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"WETH9","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"bytes","name":"path","type":"bytes"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMinimum","type":"uint256"}],"internalType":"struct ISwapRouter.ExactInputParams","name":"params","type":"tuple"}],"name":"exactInput","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"tokenIn","type":"address"},{"internalType":"address","name":"tokenOut","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMinimum","type":"uint256"},{"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"}],"internalType":"struct ISwapRouter.ExactInputSingleParams","name":"params","type":"tuple"}],"name":"exactInputSingle","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"bytes","name":"path","type":"bytes"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMaximum","type":"uint256"}],"internalType":"struct ISwapRouter.ExactOutputParams","name":"params","type":"tuple"}],"name":"exactOutput","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"tokenIn","type":"address"},{"internalType":"address","name":"tokenOut","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMaximum","type":"uint256"},{"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"}],"internalType":"struct ISwapRouter.ExactOutputSingleParams","name":"params","type":"tuple"}],"name":"exactOutputSingle","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes[]","name":"data","type":"bytes[]"}],"name":"multicall","outputs":[{"internalType":"bytes[]","name":"results","type":"bytes[]"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"refundETH","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"selfPermit","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"expiry","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"selfPermitAllowed","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"nonce","type":"uint256"},{"internalType":"uint256","name":"expiry","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"selfPermitAllowedIfNecessary","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"selfPermitIfNecessary","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountMinimum","type":"uint256"},{"internalType":"address","name":"recipient","type":"address"}],"name":"sweepToken","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountMinimum","type":"uint256"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"feeBips","type":"uint256"},{"internalType":"address","name":"feeRecipient","type":"address"}],"name":"sweepTokenWithFee","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"int256","name":"amount0Delta","type":"int256"},{"internalType":"int256","name":"amount1Delta","type":"int256"},{"internalType":"bytes","name":"_data","type":"bytes"}],"name":"uniswapV3SwapCallback","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountMinimum","type":"uint256"},{"internalType":"address","name":"recipient","type":"address"}],"name":"unwrapWETH9","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountMinimum","type":"uint256"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"feeBips","type":"uint256"},{"internalType":"address","name":"feeRecipient","type":"address"}],"name":"unwrapWETH9WithFee","outputs":[],"stateMutability":"payable","type":"function"},{"stateMutability":"payable","type":"receive"}]
WETH_ABI = [{"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"src","type":"address"},{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"wad","type":"uint256"}],"name":"withdraw","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[],"name":"deposit","outputs":[],"payable":True,"stateMutability":"payable","type":"function"},{"constant":True,"inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"payable":True,"stateMutability":"payable","type":"fallback"},{"anonymous":False,"inputs":[{"indexed":True,"name":"src","type":"address"},{"indexed":True,"name":"guy","type":"address"},{"indexed":False,"name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"src","type":"address"},{"indexed":True,"name":"dst","type":"address"},{"indexed":False,"name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"dst","type":"address"},{"indexed":False,"name":"wad","type":"uint256"}],"name":"Deposit","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"src","type":"address"},{"indexed":False,"name":"wad","type":"uint256"}],"name":"Withdrawal","type":"event"}]

def get_ethereum_data():
    # Get the current gas price
    gas_price = web3.eth.gas_price

    # Get the latest block number
    block_number = web3.eth.block_number

    # Convert gas price to gwei
    gas_fee = round(web3.from_wei(gas_price, 'gwei'), 5)
    return gas_fee, block_number

def create_wallet():
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    account = Account.from_key(private_key)
    public_key = account.address

    return public_key, private_key

def get_balance(public_key):
    # Get the balance in Wei
    balance_wei = web3.eth.get_balance(public_key)

    # Convert the balance from Wei to ETH
    balance_eth = web3.from_wei(balance_wei, 'ether')

    return balance_eth

def get_nonce(public_key):
    # Get the nonce
    nonce = web3.eth.get_transaction_count(public_key)

    return nonce

def encode_path(path, fees, exact_input):
    FEE_SIZE = 6
    if len(path) != len(fees) + 1:
        raise ValueError('path/fee lengths do not match')
    
    if not exact_input:
        path = path[::-1]
        fees = fees[::-1]

    encoded = '0x'
    for i in range(len(fees)):
        encoded += path[i][2:]
        fee = hex(fees[i])[2:].rstrip('L')
        encoded += fee.rjust(FEE_SIZE, '0')

    encoded += path[-1][2:]
    return encoded.lower()

def wrap_eth(amount, public_key, private_key):
    print("Wrapping ETH to WETH")

    weth_contract = web3.eth.contract(address=WETH_ADDRESS, abi=WETH_ABI)
    eth_amount = web3.to_wei(amount, 'ether')

    tx_data = weth_contract.encodeABI(fn_name='deposit')

    # Create a transaction object
    transaction = {
        'to': WETH_ADDRESS,
        'value': eth_amount,
        'gas': 200000,
        'gasPrice': web3.eth.gas_price,
        'nonce': web3.eth.get_transaction_count(public_key),
        'data': tx_data,
    }

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)

    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction).hex()

    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt['status']:
        print(f'Wrapping successful! {tx_hash}')
        return tx_hash
    else:
        print('Wrapping failed.')

def approve_contract(public_key, private_key, amount):
    print("Approving contract")
    # Create a contract instance for the token
    contract = web3.eth.contract(address=WETH_ADDRESS, abi=WETH_ABI)
    eth_amount = web3.to_wei(amount, 'ether')

    tx_data = contract.encodeABI(fn_name='approve', args = [UNISWAP_ROUTER_ADDRESS, eth_amount])

    # Build the transaction to call the `approve` function
    transaction = {
        'to': WETH_ADDRESS,
        'value': 0,
        'gas': 200000,
        'gasPrice': web3.eth.gas_price,
        'nonce': web3.eth.get_transaction_count(public_key),
        'data': tx_data,
    }

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)

    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction).hex()

    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    # Check the transaction status
    if receipt['status']:
        print(f'Approval successful! {tx_hash}')
        return tx_hash
    else:
        print('Approval failed.')

async def buy_token(token_address, public_key, private_key, amount):
    wrap_eth(amount, public_key, private_key)
    approve_contract(public_key, private_key, amount)

    uniswap_router = web3.eth.contract(address=UNISWAP_ROUTER_ADDRESS, abi=UNISWAP_ROUTER_ABI)


    # Set the amount of ETH you want to swap and the desired minimum amount of target token to receive
    eth_amount = web3.to_wei(amount, 'ether')
    min_token_amount = 0  # Future logic for calculating slippage and getting quote

    # Get the path for the swap (ETH to target token)
    path = [WETH_ADDRESS, token_address]
    fees = [3000]
    path_bytes = encode_path(path, fees, True)

    deadline = web3.eth.get_block('latest')['timestamp'] + 60
    swap_data = uniswap_router.encodeABI(fn_name='exactInput', args=[(path_bytes, public_key, deadline, eth_amount, min_token_amount)])

    transaction = {
        'to': UNISWAP_ROUTER_ADDRESS,
        'value': 0,
        'gas': 1000000,
        'gasPrice': web3.to_wei('2', 'gwei'),#web3.eth.gas_price,
        'nonce': web3.eth.get_transaction_count(public_key),
        'data': swap_data
    }

    # Sign and send the transaction
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction).hex()
    # Wait for the transaction to be mined
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(receipt)

    # Check the transaction status
    if receipt['status']:
        print(f'Swap successful! {tx_hash}')
        return tx_hash
    else:
        print('Swap failed.')
