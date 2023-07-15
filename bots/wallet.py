import logging
import sys
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CallbackContext
)
from validate import (validate_wallets_input)
sys.path.append("../")

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

async def import_wallet_options(update: Update, context: CallbackContext):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Please enter the private key of the wallet you want to import"
    )
    return IMPORT_WALLET

async def import_wallet(update: Update, context: CallbackContext):
    user_id = context.user_data['user_id']
    user_handle = update.effective_user.username
    private_key = update.message.text
    [public_key, e] = await validate_wallets_input(user_id, private_key)

    if e != '':
        keyboard = [
            [InlineKeyboardButton("< Back", callback_data="buy_tokens_options")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(f"Invalid input: {e}\n"
                  f"Please enter the private key of the wallet you want to import"
            ),
            reply_markup=reply_markup
        )
        return IMPORT_WALLET
    
    server.firebase_utils.insert_user_address(user_id, user_handle, public_key, private_key)
    keyboard = [
        [InlineKeyboardButton("< Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        f"Wallet Imported!"
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = text,
        reply_markup= reply_markup
    )
    return ROUTE