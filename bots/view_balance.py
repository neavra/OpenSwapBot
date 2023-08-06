import logging
import sys
import os
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CallbackContext
)
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

ROUTE, BUY_TOKENS_CONFIRMATION, SELL_TOKENS_CONFIRMATION, CUSTOM_AMOUNT, TRANSFER_TOKENS_CONFIRMATION, IMPORT_WALLET, EXPORT_WALLET = range(7)
FEES = [3000]
WETH_ADDRESS = os.getenv("WETH_ADDRESS_GOERLI") # WETH GOERLI

async def view_token_options(update: Update, context: CallbackContext):
    user_id = context.user_data["user_id"]
    message = "Please Select Wallet"
    wallet_buttons = []
    wallet_count = server.firebase_utils.get_user(user_id)['walletCount']

    for wallet in range(1, wallet_count + 1):
        wallet_buttons.append(InlineKeyboardButton(f'w{wallet}', callback_data=f'wallet_view_{wallet}'))
    
    keyboard = [
        []+wallet_buttons,
        [InlineKeyboardButton("< Back", callback_data="start")],
    ]
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    view_token_options_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = message,
        reply_markup= reply_markup
    )
    context.bot_data['view_token_options_message'] = view_token_options_message

    return ROUTE

async def view_token_balances(update: Update, context: CallbackContext):
    query= update.callback_query 
    await query.answer()
    
    try:
        await context.bot_data['view_token_options_message'].delete()
    except Exception as e:
        logger.info("Message already deleted")
    
    callback_data = query.data
    wallet_nonce = callback_data.split("_")[-1]
    user_id = context.user_data["user_id"]
    public_key = server.firebase_utils.get_user_address(user_id, wallet_nonce)
    context.user_data['public_key'] = public_key

    tokens = server.firebase_utils.get_tokens()
    text = "These are your balances:\n"
    for token in tokens:
        symbol = token["symbol"]
        balance = blockchain.web3_utils.get_balanceOf(token["address"], public_key)
        if balance != 0:
            text += f'Symbol: {symbol}\nBalance: {round(balance,5)}\n'
    # Handle no balances case
    if text == "These are your balances:\n":
        text = "You have no Available Balances!"

    keyboard = [
            [InlineKeyboardButton("< Back", callback_data="start")]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup= reply_markup
    )
    return ROUTE
