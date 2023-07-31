import logging
import sys
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CallbackContext
)
from toggle_keyboard import (init_keyboard)
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

ROUTE, BUY_TOKENS_CONFIRMATION, SELL_TOKENS_CONFIRMATION, CUSTOM_AMOUNT, TRANSFER_TOKENS_CONFIRMATION, IMPORT_WALLET, EXPORT_WALLET = range(7)
FEES = [3000]
WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6" # WETH GOERLI

async def buy_tokens_options(update: Update, context: CallbackContext):
    keyboard = await init_keyboard("Buy", context)
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
    await context.bot_data['keyboard_message']

    user_id = context.user_data.get('user_id')
    token_out = update.message.text
    amount_states = context.user_data["amount_states"]
    slippage_states = context.user_data["slippage_states"]
    wallet_states = context.user_data["wallet_states"]

    [amount_in, slippage, wallet_nonce, e] = await validate_options_input(amount_states, slippage_states, wallet_states)
    public_key = server.firebase_utils.get_user_address(user_id, wallet_nonce)

    if  e != '':
        keyboard = [
            [InlineKeyboardButton("< Back", callback_data="buy_tokens_options")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"Error: {e}",
        reply_markup= reply_markup
        )
        return ROUTE
    
    [token_out, token_out_symbol, e] = await validate_token_input(token_out)
    if e != "":
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"Could not identify the token, please input the token contract",
        )
        return BUY_TOKENS_CONFIRMATION
    

    token_in_symbol = blockchain.web3_utils.get_symbol(WETH_ADDRESS)
    
    path = [WETH_ADDRESS, token_out]
    path_bytes = blockchain.web3_utils.encode_path(path, FEES, True)
    
    try:
        amount_out_quote = await blockchain.web3_utils.get_swap_quote(path_bytes, amount_in)
        amount_out_min = await blockchain.web3_utils.calculate_slippage(amount_out_quote, slippage)

        order = {
            'user_id': user_id,
            'type': 'Buy',
            'amount_in': amount_in,
            'amount_out_min': amount_out_min,
            'slippage': slippage,
            'token_in': WETH_ADDRESS,
            'token_out': token_out,
            'token_in_symbol': token_in_symbol,
            'token_out_symbol': token_out_symbol,
            'public_key': public_key,
            'path_bytes': path_bytes,
            'status': 'PENDING',
        }
        context.user_data['order'] = order
        keyboard = [
            [InlineKeyboardButton("Confirm", callback_data="buy_tokens"),InlineKeyboardButton("< Back", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
        "Please confirm your order:\n"
        f"Wallet selected: {public_key}\n"
        f"Swap {amount_in} of {token_in_symbol} for (estimated) {round(amount_out_quote,5)} of {token_out_symbol}\n"
        )

        buy_tokens_confirmation_message = await context.bot.send_message(
                    chat_id=update.effective_chat.id, 
                    text=message, 
                    parse_mode="markdown", 
                    reply_markup=reply_markup
                )
        context.bot_data["buy_tokens_confirmation_message"] = buy_tokens_confirmation_message
        return ROUTE

    except Exception as e:
        keyboard = [
            [InlineKeyboardButton("< Back", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
        f"Error: {e}\n"
        f"When Swapping {token_in_symbol} for {token_out_symbol}"
        )

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
    await context.bot_data["buy_tokens_confirmation_message"].delete()
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
        private_key = server.firebase_utils.get_private_key(order['public_key'])
        receipt = await blockchain.web3_utils.swap_token(order['token_in'], order['token_out'], order['public_key'], private_key, order['amount_in'], order['amount_out_min'])
        tx_hash = receipt['transactionHash'].hex()
    
        amount_out = blockchain.web3_utils.parse_swap_receipt(receipt, order['token_out'], order['public_key'])
        order['status'] = 'SUCCESSFUL'
        order['tx_hash'] = tx_hash
        server.firebase_utils.insert_order(order)
        await message.delete()
        text = (
                f"Swapped {order['amount_in']} of {order['token_in_symbol']} for {amount_out} of {order['token_out_symbol']}!\n"
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
                f"When Swapping {order['token_in_symbol']} for {order['token_out_symbol']}"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text = text,
            reply_markup= reply_markup
        )
        return ROUTE
