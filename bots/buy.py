import logging
import sys
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CallbackContext
)
from toggle_keyboard import (init_keyboard_dict)
from validate import (validate_options_input, validate_token_input)
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

async def buy_tokens_options(update: Update, context: CallbackContext):
    keyboard = await init_keyboard_dict("Buy", context)
    reply_markup = InlineKeyboardMarkup(keyboard)
    keyboard_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "Please choose:", 
        reply_markup=reply_markup)
    
    request_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Please enter the token you would like to buy, you can enter a symbol i.e. BTC or the contract address"
    )
    context.bot_data['request_message'] = request_message
    context.bot_data['keyboard_message'] = keyboard_message
    return BUY_TOKENS_CONFIRMATION

async def buy_tokens_confirmation(update: Update, context: CallbackContext):
    user_id = context.user_data.get('user_id')
    token_out = update.message.text
    amount_states = context.user_data["amount_states"]
    slippage_states = context.user_data["slippage_states"]

    [amount_in, slippage] = await validate_options_input(amount_states, slippage_states)

    if  amount_in == 0 or slippage == 0:
        keyboard = [
            [InlineKeyboardButton("< Back", callback_data="buy_tokens_options")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"Please select both amount and slippage",
        reply_markup= reply_markup
        )
        return ROUTE
    
    [token_out, token_out_symbol] = await validate_token_input(token_out)
    
    if token_out == "":
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"Could not identify the token, please input the token contract",
        )
        return BUY_TOKENS_CONFIRMATION
    
    address = server.firebase_utils.get_user_address(user_id)

    token_in_symbol = blockchain.web3_utils.get_symbol(WETH_ADDRESS)
    
    path = [WETH_ADDRESS, token_out]
    path_bytes = blockchain.web3_utils.encode_path(path, FEES, True)

    order = {
        'user_id': user_id,
        'side': 'Sell',
        'amount_in': amount_in,
        'slippage': slippage,
        'token_in': WETH_ADDRESS,
        'token_out': token_out,
        'token_in_symbol': token_in_symbol,
        'token_out_symbol': token_out_symbol,
        'public_key': address[0],
        'private_key': address[1],
        'path_bytes': path_bytes,
        'status': 'PENDING',
    }
    context.user_data['order'] = order
    
    try:
        amount_out = await blockchain.web3_utils.get_swap_quote(path_bytes, amount_in)

        keyboard = [
            [InlineKeyboardButton("Confirm", callback_data="buy_tokens"),InlineKeyboardButton("< Back", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = f"""
        Please confirm your order:
        Swap {amount_in} of {token_in_symbol} for (estimated) {amount_out} of {token_out_symbol}
        Slippage: {slippage}
        """

        await context.bot.send_message(
                    chat_id=update.effective_chat.id, 
                    text=message, 
                    parse_mode="markdown", 
                    reply_markup=reply_markup
                )
        return ROUTE

    except Exception as e:
        keyboard = [
            [InlineKeyboardButton("< Back", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = f"""
        Error: {e}
        When Swapping {token_in_symbol} for {token_out_symbol}
        """

        await context.bot.send_message(
                    chat_id=update.effective_chat.id, 
                    text=message, 
                    parse_mode="markdown", 
                    reply_markup=reply_markup
                )
        return ROUTE

async def buy_tokens(update: Update, context: CallbackContext):
    if update.callback_query:
        # Handling CallbackQueryHandler case
        query = update.callback_query
        await query.answer()

    # Send loading message to user
    loading_message = "Executing Swap, this might take a while..."
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text=loading_message)

    keyboard = [
        [InlineKeyboardButton("< Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    order = context.user_data['order']
    logger.info(f'Processing Order: {order}')
    try:
        receipt = await blockchain.web3_utils.swap_token(order['token_in'], order['token_out'], order['public_key'], order['private_key'], order['amount_in'])
        tx_hash = receipt['transactionHash'].hex()
    
        amount_out = blockchain.web3_utils.parse_swap_receipt(receipt, order['token_out'], order['public_key'])
        order['status'] = 'SUCCESSFUL'
        server.firebase_utils.insert_order(order)
        await message.delete()
        text = f"""
                Swapped {order['amount_in']} of {order['token_in_symbol']} for {amount_out} of {order['token_out_symbol']}!
                Tx hash: {tx_hash}
                """
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text = text,
            reply_markup= reply_markup
        )
        return ROUTE

    except Exception as e:
        order['status'] = 'UNSUCCESSFUL'
        server.firebase_utils.insert_order(order)

        await message.delete()
        text = f"""
                Error: {e}
                When Swapping {order['token_in_symbol']} for {order['token_out_symbol']}
                """
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text = text,
            reply_markup= reply_markup
        )
        return ROUTE
