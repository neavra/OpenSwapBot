import logging
import sys
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

ROUTE, BUY_TOKENS_CONFIRMATION, SELL_TOKENS_CONFIRMATION, CUSTOM_AMOUNT = range(4)
FEES = [3000]
WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6" # WETH GOERLI

async def transfer_tokens_options(update: Update, context: CallbackContext):
    message = "Please Select Token"
    keyboard = []
    tokens = server.firebase_utils.get_tokens()
    public_key = context.user_data['public_key']

    for token in tokens:
        symbol = token["symbol"]
        balance = blockchain.web3_utils.get_balanceOf(token["address"], public_key)
        context.user_data['balance'] = balance
        if balance != 0:
            keyboard += [InlineKeyboardButton(f'{symbol}', callback_data= 'select_amount')],
    if keyboard == []:
        message = "You have no detected balances!"

    keyboard += [InlineKeyboardButton("< Back", callback_data="start")],
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = message,
        reply_markup= reply_markup
    )

    return ROUTE    

async def select_amount(update: Update, context: CallbackContext):
    message = 'Please select amount'

    keyboard = [
        [InlineKeyboardButton(f'25%', callback_data='transfer_25%'),
         InlineKeyboardButton(f'50%', callback_data='transfer_50%'),
         InlineKeyboardButton(f'75%', callback_data='transfer_75%'),
         InlineKeyboardButton(f'100%', callback_data='transfer_100%')
         ],
        [InlineKeyboardButton('< Back', callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = message,
        reply_markup= reply_markup)

    return ROUTE

async def transfer_tokens_confirmation(update: Update, context: CallbackContext):
    # Handle logic for amount calculations and fetch token selected
    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data="buy_tokens"),InlineKeyboardButton("< Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
    "Please confirm your order:\n"
    f"Transfers\n"
    f"Slippage"
    )

    await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=message, 
                parse_mode="markdown", 
                reply_markup=reply_markup
            )
    return ROUTE