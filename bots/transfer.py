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

async def transfer_tokens_options(update: Update, context: CallbackContext):
    user_id = context.user_data["user_id"]
    message = "Please Select Wallet"
    wallet_buttons = []
    wallet_count = server.firebase_utils.get_user(user_id)['walletCount']

    for wallet in range(1, wallet_count + 1):
        wallet_buttons.append(InlineKeyboardButton(f'w{wallet}', callback_data=f'wallet_transfer_{wallet}'))
    
    keyboard = [
        []+wallet_buttons,
        [InlineKeyboardButton("< Back", callback_data="start")],
    ]
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    transfer_tokens_options_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = message,
        reply_markup= reply_markup
    )
    context.bot_data["transfer_tokens_options_message"] = transfer_tokens_options_message
    return ROUTE   
 
async def select_token(update: Update, context: CallbackContext):
    query= update.callback_query 
    await query.answer()
    await context.bot_data["transfer_tokens_options_message"].delete()

    callback_data = query.data
    wallet_nonce = callback_data.split("_")[-1]
    user_id = context.user_data["user_id"]
    public_key = server.firebase_utils.get_user_address(user_id, wallet_nonce)
    context.user_data['public_key'] = public_key
    message = f"You have selected {public_key}"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = message,
    )
 
    message = "Please Select Token"
    keyboard = []
    tokens = server.firebase_utils.get_tokens()

    for token in tokens:
        symbol = token["symbol"]
        balance = blockchain.web3_utils.get_balanceOf(token["address"], public_key)
        if balance != 0:
            keyboard += [InlineKeyboardButton(f'{symbol}', callback_data= f'select_transfer_amount_{symbol}')],
    if keyboard == []:
        message = "You have no detected balances!"

    keyboard += [InlineKeyboardButton("< Back", callback_data="start")],
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    select_token_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = message,
        reply_markup= reply_markup
    )
    context.bot_data["select_token_message"] = select_token_message
    return ROUTE

async def select_transfer_amount(update: Update, context: CallbackContext):
    query= update.callback_query 
    await query.answer()
    await context.bot_data["select_token_message"].delete()

    callback_data = query.data
    symbol = callback_data.split("_")[-1]
    context.user_data['symbol'] = symbol
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
    select_transfer_amount_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = message,
        reply_markup= reply_markup
    )
    context.bot_data["select_transfer_amount_message"] = select_transfer_amount_message
    return ROUTE

async def select_transfer_address(update: Update, context: CallbackContext):
    query= update.callback_query 
    await query.answer()
    await context.bot_data["select_transfer_amount_message"].delete()

    callback_data = query.data
    amount_percentage = callback_data.split("_")[-1]
    symbol = context.user_data['symbol']
    public_key = context.user_data['public_key']
    # THis method should be extensible to buy and sell amount
    amount = await calculate_amount(amount_percentage, symbol, public_key)
    context.user_data['amount'] = amount

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Please enter the wallet address that you would like to send to"
    )
    return TRANSFER_TOKENS_CONFIRMATION

async def transfer_tokens_confirmation(update: Update, context: CallbackContext):
    public_key = context.user_data['public_key']
    to_address = update.message.text
    token_symbol =  context.user_data['symbol']
    token = server.firebase_utils.get_token(token_symbol)
    user_id = context.user_data['user_id']

    amount = context.user_data['amount']
    
    keyboard = [
        [InlineKeyboardButton("Confirm", callback_data="transfer_tokens"),InlineKeyboardButton("< Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
    "Please confirm your order:\n"
    f"Transfer {amount} of {token_symbol} from {public_key} to {to_address}\n"
    )

    order = {
        'user_id': user_id,
        'type': 'Transfer',
        'amount': amount,
        'token_address': token['address'],
        'token_symbol': token_symbol,
        'from_address': public_key,
        'to_address': to_address,
        'status': 'PENDING',
    }
    context.user_data['order'] = order

    transfer_tokens_confirmation_message = await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=message, 
                parse_mode="markdown", 
                reply_markup=reply_markup
            )
    context.bot_data["transfer_tokens_confirmation_message"] = transfer_tokens_confirmation_message
    return ROUTE

async def transfer_tokens(update: Update, context: CallbackContext):
    await context.bot_data["transfer_tokens_confirmation_message"].delete()
    order = context.user_data['order']

    loading_message = "Transferring Tokens, this might take a while..."
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text=loading_message)

    keyboard = [
        [InlineKeyboardButton("< Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    logger.info(f'Processing Order: {order}')

    try:
        public_key = context.user_data['public_key']
        private_key = server.firebase_utils.get_private_key(public_key)
        if order['token_address'] == "0x0000000000000000000000000000000000000000":
            tx_hash = await blockchain.web3_utils.transfer_token(order['from_address'], order['to_address'], order['amount'], private_key)
        else:
            tx_hash = await blockchain.web3_utils.transfer_token(order['from_address'], order['to_address'], order['amount'], private_key, order['token_address'])
        order['status'] = 'SUCCESSFUL'
        order['tx_hash'] = tx_hash
        server.firebase_utils.insert_order(order)
        await message.delete()
        text = (
                f"Transferred  {order['amount']} of {order['token_symbol']} from {order['from_address']} to {order['to_address']}!\n"
                f"Tx hash: {tx_hash}\n"
                )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text = text,
            reply_markup= reply_markup
        )
        return ROUTE

    except Exception as e:
        order['status'] = 'UNSUCCESSFUL'
        order['tx_hash'] = ''
        server.firebase_utils.insert_order(order)

        await message.delete()
        text = (
                f"Error: {e}\n"
                f"When Transferring {order['amount']} of {order['token_symbol']} from {order['from_address']} to {order['to_address']}"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text = text,
            reply_markup= reply_markup
        )
        return ROUTE
    
async def calculate_amount(amount_percentage, symbol, public_key):
    amount_percentage = amount_percentage.strip('%')
    percentage = float(amount_percentage) / 100
    if symbol == 'ETH': # In the case of eth need to leave some eth for gas
        balance = float(blockchain.web3_utils.get_eth_balance(public_key)) - 0.0001
    else:
        token = server.firebase_utils.get_token(symbol)
        address = token['address']
        balance = blockchain.web3_utils.get_balanceOf(address, public_key)

    amount = round(float(balance) * percentage,18)
    return amount
