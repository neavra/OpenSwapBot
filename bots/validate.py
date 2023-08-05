import logging
import sys
import os
from dotenv import load_dotenv

sys.path.append("./")

import blockchain.web3_utils
import server.firebase_utils

load_dotenv()

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ROUTE, BUY_TOKENS_CONFIRMATION, SELL_TOKENS_CONFIRMATION, CUSTOM_AMOUNT, TRANSFER_TOKENS_CONFIRMATION, IMPORT_WALLET, EXPORT_WALLET = range(7)
FEES = [3000]
WETH_ADDRESS = os.getenv("WETH_ADDRESS_GOERLI") # WETH GOERLI

async def validate_options_input(amount_states, slippage_states, wallet_states):
    amount_in = 0
    slippage = 0
    wallet_nonce = 0
    try:
        for key, value in amount_states.items():
            if value == True:
                val = key.split('_')[-1]
                amount_in = float(val)
        for key, value in slippage_states.items():
            if value == True:
                val = key.split('_')[-1]
                if val =='auto':
                    val = 5
                slippage = float(val)
        for key, value in wallet_states.items():
            if value ==True:
                val = key.split('_')[-1]
                wallet_nonce = val
        if amount_in == 0:
            raise ValueError("Amount is not selected")
        if slippage == 0:
            raise ValueError("Slippage is not selected")
        if wallet_nonce == 0:
            raise ValueError("Wallet is not selected")
        if amount_in <= 0:
            raise ValueError("Amount cannot be negative")
        
        return [amount_in, slippage, wallet_nonce, '']
    except Exception as e:
        logger.info(f'Error when validating options input: {e}')
        return [0,0,0,e]

async def validate_token_input(token_input):
    # Deals with both Symbol and Contract case
    try:
        if token_input.startswith("0x") and len(token_input) == 42:
            symbol = blockchain.web3_utils.get_symbol(token_input)
            decimal = blockchain.web3_utils.get_decimal(token_input)
            server.firebase_utils.insert_token(symbol, token_input, decimal, 'Goerli')
            return [token_input, symbol, ""]
        else:
            token_input = token_input.upper()
            if token_input == "WETH":
                raise ValueError('Wrap your ETH to get WETH instead of swapping')
            token = server.firebase_utils.get_token(token_input)
            if not token: # If token object is not found
                raise ValueError('Token not recognised, please input contract address')
            return [token["address"],token["symbol"], ""] # Return the contract address
    except Exception as e:
        logger.info(f"Error when validating token_input: {e}")
        return ["","",e]
    
async def check_number_of_wallets(user_id):
    walletCount = server.firebase_utils.get_user(user_id)['walletCount']
    try:
        if walletCount >= 5:
            raise ValueError("Hit max wallets")
        return ''
    except Exception as e:
        logger.info(f"User has hit the max limit of wallets: {walletCount}")
        return e

async def validate_wallets_input(user_id ,private_key):
    if private_key[:2] != '0x':
        private_key = '0x' +private_key
    try:
        if len(private_key) != 66:
            raise ValueError("Incorrect length of private key")
        else:
            public_key = blockchain.web3_utils.derive_public_key(private_key)
        # Check for repeated imports
        addresses = server.firebase_utils.get_user_addresses(user_id)
        if public_key in [address for address in addresses]:
            raise ValueError("Wallet already exists")
        return [public_key, '']
    except Exception as e:
        logger.info(f'Error when validating wallets input: {e}')
        return ['0x0', e]