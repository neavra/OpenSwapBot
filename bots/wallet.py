import logging
import asyncio
import sys
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CallbackContext
)
from validate import (validate_wallets_input, check_number_of_wallets)
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
WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6" # WETH GOERLI

async def import_wallet_options(update: Update, context: CallbackContext):
    user_id = context.user_data['user_id']
    e = await check_number_of_wallets(user_id)
    if e != '':
        keyboard = [
            [InlineKeyboardButton("< Back", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(f"Sorry! Each user can only have a max of 5 wallets"
            ),
            reply_markup=reply_markup
        )
        return IMPORT_WALLET

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

async def export_wallet_options(update: Update, context: CallbackContext):
    user_id = context.user_data["user_id"]
    message = "Please Select Wallet"
    wallet_buttons = []
    wallet_count = server.firebase_utils.get_user(user_id)['walletCount']

    for wallet in range(1, wallet_count + 1):
        wallet_buttons.append(InlineKeyboardButton(f'w{wallet}', callback_data=f'export_wallet_{wallet}'))
    
    keyboard = [
        []+wallet_buttons,
        [InlineKeyboardButton("< Back", callback_data="start")],
    ]
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = message,
        reply_markup= reply_markup
    )

    return EXPORT_WALLET

async def export_wallet_confirmation(update: Update, context: CallbackContext):
    query= update.callback_query 
    await query.answer()
    callback_data = query.data
    wallet_nonce = callback_data.split("_")[-1]
    user_id = context.user_data["user_id"]
    public_key = server.firebase_utils.get_user_address(user_id, wallet_nonce)
    context.user_data['public_key'] = public_key

    keyboard = [
            [InlineKeyboardButton("Confirm", callback_data="export_wallet"),InlineKeyboardButton("< Back", callback_data="start")]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
    f"Wallet selected: {public_key}\n"
    f"By clicking continue, your private key will be sent to you.\n"
    f"NEVER REVEAL UR PRIVATE KEY TO ANYONE. YOU WILL LOSE ALL YOUR FUNDS\n"
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=message, 
        parse_mode="markdown", 
        reply_markup=reply_markup
    )
    return EXPORT_WALLET

async def export_wallet(update: Update, context: CallbackContext):
    public_key = context.user_data['public_key']
    private_key = server.firebase_utils.get_private_key(public_key)
    message = (
    f"Private Key: {private_key}\n"
    )

    sent_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        parse_mode="markdown",
    )

    # Wait for 10 seconds
    await asyncio.sleep(10)

    # Delete the sent message
    await sent_message.delete()
    return ROUTE

