import logging
import os
import sys
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler,CallbackContext, CallbackQueryHandler, ConversationHandler, MessageHandler, ContextTypes, filters
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

TELE_TOKEN = os.getenv("TELE_TOKEN")

ROUTE, BUY_TOKENS_CONFIRMATION, SELL_TOKENS_CONFIRMATION = range(3)
FEES = [3000]
WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6" # WETH GOERLI
# Function to handle the /start command
async def start(update: Update, context: CallbackContext):
    if update.message:
        # Handling CommandHandler case
        user_id = update.message.from_user.id
    elif update.callback_query:
        # Handling CallbackQueryHandler case
        query = update.callback_query
        await query.answer()
        user_id = update.callback_query.from_user.id
    else:
        # Neither message nor callback query is available
        user_id = None
    user_handle = update.effective_user.username
    context.user_data['user_id'] = user_id

    gas_fee, block_number = blockchain.web3_utils.get_ethereum_data()
    address = server.firebase_utils.get_user_address(user_id)

    if not address:
        # Onboard new user
        new_public_key, new_private_key = blockchain.web3_utils.create_wallet()
        server.firebase_utils.insert_user_address(user_id, user_handle, new_public_key, new_private_key)
        address = server.firebase_utils.get_user_address(user_id)

    public_key = address[0]
    balance = blockchain.web3_utils.get_eth_balance(public_key)
    transaction = blockchain.web3_utils.get_nonce(public_key)

    keyboard = [
        [InlineKeyboardButton("Buy Tokens", callback_data="buy_tokens_options"),InlineKeyboardButton("Sell Tokens", callback_data="sell_tokens_options")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = f"""
    Current Gas Fees: {gas_fee} gwei
    Current Block Number: {block_number}
    ═══ Your Wallets ═══
    ▰ Wallet - w1
    Balance:
    {balance} ETH
    Transactions:
    {transaction}
    Address: {public_key}
    """

    await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=message, 
                parse_mode="markdown", 
                reply_markup=reply_markup
            )
    return ROUTE

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
            [InlineKeyboardButton("< Back", callback_data="start")]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I did not understand that command",
        reply_markup= reply_markup
    )

async def buy_tokens_options(update: Update, context: CallbackContext):
    toggle_states = {
        'toggle_0.001' : False,
        'toggle_0.002' : False,
    }
    slippage_states= {
        'slippage_10' : False,
        'slippage_20' : False,
        'slippage_30' : False,
    }
    emoji ={
        'toggle_0.001' : '',
        'toggle_0.002' : '',
        'slippage_10' : '',
        'slippage_20' : '',
        'slippage_30' : '',
    
    }
    
    context.user_data["toggle_states"] = toggle_states
    context.user_data["slippage_states"] = slippage_states
    context.user_data["side"] = "Buy"
    context.user_data["emoji"] = emoji
    keyboard = [
        [InlineKeyboardButton(f"Buy Amount", callback_data="empty")],
        [
            InlineKeyboardButton("0.001", callback_data="toggle_0.001"),
            InlineKeyboardButton("0.002", callback_data="toggle_0.002"),
        ],
        [InlineKeyboardButton("Slippage", callback_data="empty")],
        [
            InlineKeyboardButton("10%", callback_data="slippage_10"),
            InlineKeyboardButton("20%", callback_data="slippage_20"),
            InlineKeyboardButton("30%", callback_data="slippage_30"),

        ],
        [InlineKeyboardButton("Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "Please choose:", 
        reply_markup=reply_markup)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Please enter the token you would like to buy, you can enter a symbol i.e. BTC or the contract address"
    )
    return BUY_TOKENS_CONFIRMATION

async def buy_tokens_confirmation(update: Update, context: CallbackContext):
    user_id = context.user_data.get('user_id')
    token_out = update.message.text
    toggle_states = context.user_data["toggle_states"]
    slippage_states = context.user_data["slippage_states"]
    
    [amount_in, slippage] = await validate_options_input(toggle_states, slippage_states)

    if  amount_in == 0 or slippage == 0:
        keyboard = [
            [InlineKeyboardButton("< Back", callback_data="buy_tokens_options")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"Please select an amount and slippage",
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

async def sell_tokens_options(update: Update, context: CallbackContext):
    toggle_states = {
        'toggle_0.001' : False,
        'toggle_0.002' : False,
    }
    slippage_states= {
        'slippage_10' : False,
        'slippage_20' : False,
        'slippage_30' : False,
    }
    emoji ={
        'toggle_0.001' : '',
        'toggle_0.002' : '',
        'slippage_10' : '',
        'slippage_20' : '',
        'slippage_30' : '',
    
    }
    
    context.user_data["toggle_states"] = toggle_states
    context.user_data["slippage_states"] = slippage_states
    context.user_data["emoji"] = emoji
    context.user_data["side"] = 'Sell'
    keyboard = [
        [InlineKeyboardButton(f"Sell Amount", callback_data="empty")],
        [
            InlineKeyboardButton("0.001", callback_data="toggle_0.001"),
            InlineKeyboardButton("0.002", callback_data="toggle_0.002"),
        ],
        [InlineKeyboardButton("Slippage", callback_data="empty")],
        [
            InlineKeyboardButton("10%", callback_data="slippage_10"),
            InlineKeyboardButton("20%", callback_data="slippage_20"),
            InlineKeyboardButton("30%", callback_data="slippage_30"),

        ],
        [InlineKeyboardButton("Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "Please choose:", 
        reply_markup=reply_markup)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Please enter the token you would like to sell"
    )
    return SELL_TOKENS_CONFIRMATION

async def sell_tokens_confirmation(update: Update, context: CallbackContext):
    user_id = context.user_data.get('user_id')
    token_in = update.message.text
    toggle_states = context.user_data["toggle_states"]
    slippage_states = context.user_data["slippage_states"]

    [amount_in, slippage] = await validate_options_input(toggle_states, slippage_states)

    if  amount_in == 0 or slippage == 0:
        keyboard = [
            [InlineKeyboardButton("< Back", callback_data="buy_tokens_options")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"Please select an amount and slippage",
        reply_markup= reply_markup
        )
        return ROUTE

    [token_in, token_in_symbol] = await validate_token_input(token_in)

    if token_in == "":
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"Could not identify the token, please input the token contract",
        )
        return BUY_TOKENS_CONFIRMATION
    
    address = server.firebase_utils.get_user_address(user_id)

    token_out_symbol = blockchain.web3_utils.get_symbol(WETH_ADDRESS)
    
    path = [token_in, WETH_ADDRESS]
    path_bytes = blockchain.web3_utils.encode_path(path, FEES, True)

    order = {
        'user_id': user_id,
        'side': 'Sell',
        'amount_in': amount_in,
        'slippage': slippage,
        'token_in': token_in,
        'token_out': WETH_ADDRESS,
        'token_in_symbol': token_in_symbol,
        'token_out_symbol': token_out_symbol,
        'public_key': address[0],
        'private_key': address[1],
        'path_bytes': path_bytes,
    }
    context.user_data['order'] = order

    try:
        amount_out = await blockchain.web3_utils.get_swap_quote(path_bytes, amount_in)

        keyboard = [
            [InlineKeyboardButton("Confirm", callback_data="sell_tokens"),InlineKeyboardButton("Go back", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = f"""
        Please confirm your order:
        Swap {amount_in} of {token_in_symbol} for (estimated) {amount_out} of {token_out_symbol}
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
            [InlineKeyboardButton("Go back", callback_data="start")]
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

async def sell_tokens(update: Update, context: CallbackContext):
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

async def toggle(update: Update, context: CallbackContext):
    query= update.callback_query 
    await query.answer()
    callback_data = query.data
    category = callback_data[:3]

    toggle_states = context.user_data["toggle_states"]
    slippage_states = context.user_data["slippage_states"]
    side = context.user_data["side"]
    emoji = context.user_data["emoji"]
    if category == 'tog':
        # Prevent mulitple selection of the same category and toggles switch
        toggle_states[callback_data] = not toggle_states[callback_data]
        if toggle_states[callback_data]:
            for key, value in toggle_states.items():
                if value and key != callback_data:
                    toggle_states[key] = False   
    elif category == 'sli':
        slippage_states[callback_data] = not slippage_states[callback_data]
        if slippage_states[callback_data]:
            for key, value in slippage_states.items():
                if value and key != callback_data:
                    slippage_states[key] = False
    
    emoji["toggle_0.001"] = '\u2705' if toggle_states["toggle_0.001"] else ''
    emoji["toggle_0.002"] = '\u2705' if toggle_states["toggle_0.002"] else ''
    emoji["slippage_10"] = '\u2705' if slippage_states["slippage_10"] else ''
    emoji["slippage_20"] = '\u2705' if slippage_states["slippage_20"] else ''
    emoji["slippage_30"] = '\u2705' if slippage_states["slippage_30"] else ''
    keyboard = [
        [InlineKeyboardButton(f"{side} Amount", callback_data="empty")],
        [
            InlineKeyboardButton(f'0.001 {emoji["toggle_0.001"]}', callback_data="toggle_0.001"),
            InlineKeyboardButton(f'0.002 {emoji["toggle_0.002"]}', callback_data="toggle_0.002"),
        ],
        [InlineKeyboardButton("Slippage", callback_data="empty")],
        [
            InlineKeyboardButton(f'10% {emoji["slippage_10"]}', callback_data="slippage_10"),
            InlineKeyboardButton(f'20% {emoji["slippage_20"]}', callback_data="slippage_20"),
            InlineKeyboardButton(f'30% {emoji["slippage_30"]}', callback_data="slippage_30"),

        ],
        [InlineKeyboardButton("Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text = "Please choose:", 
        reply_markup=reply_markup)
    if side == "Sell":
        return SELL_TOKENS_CONFIRMATION
    else:
        return BUY_TOKENS_CONFIRMATION

async def validate_options_input(toggle_states, slippage_states):
    amount_in = 0
    slippage = 0
    for key, value in toggle_states.items():
        if value == True:
            amount_in = float(key[-5:])
    for key, value in slippage_states.items():
        if value == True:
            slippage = int(key[-2:])

    if amount_in <= 0 or (slippage <= 0 or slippage>=100):
        return [0,0]
    return [amount_in, slippage]

async def validate_token_input(token_input):
    # Deals with both Symbol and Contract case
    try:
        if isinstance(token_input, str) and token_input.startswith("0x") and len(token_input) == 42:
            logger.info("This is a contract address")
            symbol = blockchain.web3_utils.get_symbol(token_input)
            server.firebase_utils.insert_token(symbol, token_input, 18, 'Goerli')
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


def main():
    app = ApplicationBuilder().token(TELE_TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start)
        ],
        states= {
            ROUTE: {
                CallbackQueryHandler(start, pattern = "^start$"),
                CallbackQueryHandler(buy_tokens_options, pattern="^buy_tokens_options$"),
                CallbackQueryHandler(sell_tokens_options, pattern="^sell_tokens_options$"),
                CallbackQueryHandler(sell_tokens, pattern="^sell_tokens$"),
                CallbackQueryHandler(buy_tokens, pattern="^buy_tokens$"),
            },
            BUY_TOKENS_CONFIRMATION: {
                MessageHandler(filters.TEXT, buy_tokens_confirmation),
                CallbackQueryHandler(start, pattern = "^start$"),
                CallbackQueryHandler(toggle, pattern="^toggle_0.001$"),
                CallbackQueryHandler(toggle, pattern="^toggle_0.002$"),
                CallbackQueryHandler(toggle, pattern="^slippage_10$"),
                CallbackQueryHandler(toggle, pattern="^slippage_20$"),
                CallbackQueryHandler(toggle, pattern="^slippage_30$"),
                },

            SELL_TOKENS_CONFIRMATION: {
                MessageHandler(filters.TEXT, sell_tokens_confirmation),
                CallbackQueryHandler(start, pattern = "^start$"),
                CallbackQueryHandler(toggle, pattern="^toggle_0.001$"),
                CallbackQueryHandler(toggle, pattern="^toggle_0.002$"),
                CallbackQueryHandler(toggle, pattern="^slippage_10$"),
                CallbackQueryHandler(toggle, pattern="^slippage_20$"),
                CallbackQueryHandler(toggle, pattern="^slippage_30$"),
            },
        },
        fallbacks= [MessageHandler(filters.TEXT, unknown)]
    )
    app.add_handler(conversation_handler)

    app.run_polling()
    return

if __name__ == '__main__':
    main()
