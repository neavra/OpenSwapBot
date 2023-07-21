import logging
import sys
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

ROUTE, BUY_TOKENS_CONFIRMATION, SELL_TOKENS_CONFIRMATION, CUSTOM_AMOUNT, TRANSFER_TOKENS_CONFIRMATION, IMPORT_WALLET = range(6)
FEES = [3000]
WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6" # WETH GOERLI

async def validate_options_input(amount_states, slippage_states):
    amount_in = 0
    slippage = 0
    try:
        for key, value in amount_states.items():
            if value == True:
                amount_in = float(key.split('_')[-1])
        for key, value in slippage_states.items():
            if value == True:
                slippage = float(key.split('_')[-1])

        if amount_in == 0:
            raise ValueError("Amount is not selected")
        if slippage == 0:
            raise ValueError("Slippage is not selected")

        if amount_in <= 0:
            raise ValueError("Amount cannot be negative")
        return [amount_in, slippage, '']
    except Exception as e:
        logger.info(f'Error when validating options input: {e}')
        return [0,0,e]

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
            token = server.firebase_utils.get_token(token_input)
            if not token: # If token object is not found
                raise ValueError('Token not recognised')
            return [token["address"],token["symbol"], ""] # Return the contract address
    except Exception as e:
        logger.info(f"Error when validating token_input: {e}")
        return ["","",e]

async def validate_wallets_input(user_id ,private_key):
    if private_key[:2] != '0x':
        private_key = '0x' +private_key
    try:
        if len(private_key) != 66:
            raise ValueError("Incorrect length of private key")
        else:
            public_key = blockchain.web3_utils.derive_public_key(private_key)
        # Check for repeated imports
        addresses = server.firebase_utils.get_user_address(user_id)
        if public_key in [address for address in addresses]:
            raise ValueError("Wallet already exists")
        return [public_key, '']
    except Exception as e:
        logger.info(f'Error when validating wallets input: {e}')
        return ['0x0', e]