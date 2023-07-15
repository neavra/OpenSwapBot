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

ROUTE, BUY_TOKENS_CONFIRMATION, SELL_TOKENS_CONFIRMATION, CUSTOM_AMOUNT, TRANSFER_TOKENS_CONFIRMATION = range(5)
FEES = [3000]
WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6" # WETH GOERLI

async def validate_options_input(amount_states, slippage_states):
    amount_in = 0
    slippage = 0
    try:
        for key, value in amount_states.items():
            if value == True:
                amount_in = float(key[7:])
        for key, value in slippage_states.items():
            if value == True:
                slippage = float(key[-2:])

        if amount_in == 0:
            raise ValueError("Amount is not selected")
        if slippage == 0:
            raise ValueError("Slippage is not selected")
    except Exception as e:
        logger.info(f'Error when validating options input: {e}')
        return [0,0]
    if amount_in <= 0 or (slippage <= 0 or slippage>=100):
        return [0,0]
    return [amount_in, slippage]

async def validate_token_input(token_input):
    # Deals with both Symbol and Contract case
    try:
        if isinstance(token_input, str) and token_input.startswith("0x") and len(token_input) == 42:
            symbol = blockchain.web3_utils.get_symbol(token_input)
            decimal = blockchain.web3_utils.get_decimal(token_input)
            server.firebase_utils.insert_token(symbol, token_input, decimal, 'Goerli')
            return [token_input, symbol]
        else:
            token_input = token_input.upper()
            token = server.firebase_utils.get_token(token_input)
            if not token: # If token object is not found
                return ["",""]
            return [token["address"],token["symbol"]] # Return the contract address
    except Exception as e:
        logger.info(f"Error when validating token_input: {e}")
        return ""
