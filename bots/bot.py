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

TELE_TOKEN = os.getenv("TELE_TOKEN")

ROUTE, BUY_TOKENS_CONFIRMATION, BUY_TOKENS, SELL_TOKENS_CONFIRMATION = range(4)
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
    context.user_data['user_id'] = user_id

    gas_fee, block_number = blockchain.web3_utils.get_ethereum_data()
    address = server.firebase_utils.get_user_address(user_id)
    

    if not address:
        # Onboard new user
        new_public_key, new_private_key = blockchain.web3_utils.create_wallet()
        server.firebase_utils.insert_user_address(user_id, new_public_key, new_private_key)
        address = server.firebase_utils.get_user_address(user_id)

    public_key = address[0]
    balance = blockchain.web3_utils.get_balance(public_key)
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
            [InlineKeyboardButton("Go back", callback_data="start")]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I did not understand that command",
        reply_markup= reply_markup
    )

async def buy_tokens_options(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Buy Amount", callback_data="start")],
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2"),
        ],
        [InlineKeyboardButton("Slippage", callback_data="start")],
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2"),
            InlineKeyboardButton("Option 3", callback_data="3"),

        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "Please choose:", 
        reply_markup=reply_markup)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please enter a contract address"
    )
    return BUY_TOKENS_CONFIRMATION

async def buy_tokens_confirmation(update: Update, context: CallbackContext):
    # To be refactored into options menu
    ##########################################################################################################################################################
    user_id = context.user_data.get('user_id')
    token_out = update.message.text

    address = server.firebase_utils.get_user_address(user_id)
    public_key = address[0]
    private_key = address[1]

    context.user_data['amount_in'] = 0.0001
    context.user_data['token_in'] = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"
    context.user_data['token_out'] = token_out
    context.user_data['public_key'] = public_key
    context.user_data['private_key'] = private_key

    amount_in = context.user_data['amount_in']
    amount_in = 0.0001
    token_in = context.user_data['token_in']
    token_out = context.user_data['token_out']

    token_in_symbol = blockchain.web3_utils.get_symbol(token_in)
    token_out_symbol = blockchain.web3_utils.get_symbol(token_out)
    fees = [3000]

    context.user_data['token_in_symbol'] = token_in_symbol
    context.user_data['token_out_symbol'] = token_out_symbol
    context.user_data['fees'] = fees

    validation_result = blockchain.web3_utils.validate_params(token_in, token_out, public_key, amount_in)

    if validation_result:
        await message.delete()
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"{str(validation_result)}",
        reply_markup= reply_markup
        )
        return
    
    path = [token_in, token_out]
    path_bytes = blockchain.web3_utils.encode_path(path, fees, True)

    context.user_data['path_bytes'] = path_bytes
    ##########################################################################################################################################################

    try:
        amount_out = await blockchain.web3_utils.get_swap_quote(path_bytes, amount_in)

        keyboard = [
            [InlineKeyboardButton("Confirm", callback_data="buy_tokens"),InlineKeyboardButton("Go back", callback_data="start")]
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

async def buy_tokens(update: Update, context: CallbackContext):
    if update.callback_query:
        # Handling CallbackQueryHandler case
        query = update.callback_query
        await query.answer()

    user_id = context.user_data.get('user_id')
    # Send loading message to user
    loading_message = "Executing Swap, this might take a while..."
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text=loading_message)

    keyboard = [
        [InlineKeyboardButton("Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    public_key = context.user_data['public_key']
    private_key = context.user_data['private_key']
    amount_in = context.user_data['amount_in']
    token_in = context.user_data['token_in']
    token_out = context.user_data['token_out']
    
    token_in_symbol = context.user_data['token_in_symbol']
    token_out_symbol = context.user_data['token_out_symbol']

    try:
        receipt = await blockchain.web3_utils.swap_token(token_in, token_out, public_key, private_key, amount_in)
        tx_hash = receipt['transactionHash'].hex()
    
        amount_out = blockchain.web3_utils.parse_swap_receipt(receipt, token_out, public_key)
        await message.delete()
        text = f"""
                Swapped {amount_in} of {token_in_symbol} for {amount_out} of {token_out_symbol}!
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
                When Swapping {token_in_symbol} for {token_out_symbol}
                Tx Hash: {tx_hash}
                """
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text = text,
            reply_markup= reply_markup
        )
        return ROUTE

async def sell_tokens_options(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("sell Amount", callback_data="start")],
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2"),
        ],
        [InlineKeyboardButton("Slippage", callback_data="start")],
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2"),
            InlineKeyboardButton("Option 3", callback_data="3"),

        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "Please choose:", 
        reply_markup=reply_markup)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please enter the token you would like to sell"
    )
    return SELL_TOKENS_CONFIRMATION

async def sell_tokens_confirmation(update: Update, context: CallbackContext):
    # To be refactored into options menu
    ##########################################################################################################################################################
    user_id = context.user_data.get('user_id')
    token_in = update.message.text

    address = server.firebase_utils.get_user_address(user_id)
    public_key = address[0]
    private_key = address[1]

    context.user_data['amount_in'] = 0.0001
    context.user_data['token_in'] = token_in
    context.user_data['token_out'] = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6" # WETH
    context.user_data['public_key'] = public_key
    context.user_data['private_key'] = private_key

    amount_in = context.user_data['amount_in']
    amount_in = 0.0001
    token_in = context.user_data['token_in']
    token_out = context.user_data['token_out']

    token_in_symbol = blockchain.web3_utils.get_symbol(token_in)
    token_out_symbol = blockchain.web3_utils.get_symbol(token_out)
    fees = [3000]

    context.user_data['token_in_symbol'] = token_in_symbol
    context.user_data['token_out_symbol'] = token_out_symbol
    context.user_data['fees'] = fees

    validation_result = blockchain.web3_utils.validate_params(token_in, token_out, public_key, amount_in)

    if validation_result:
        await message.delete()
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"{str(validation_result)}",
        reply_markup= reply_markup
        )
        return
    
    path = [token_in, token_out]
    path_bytes = blockchain.web3_utils.encode_path(path, fees, True)

    context.user_data['path_bytes'] = path_bytes
    ##########################################################################################################################################################

    try:
        amount_out = await blockchain.web3_utils.get_swap_quote(path_bytes, amount_in)

        keyboard = [
            [InlineKeyboardButton("Confirm", callback_data="buy_tokens"),InlineKeyboardButton("Go back", callback_data="start")]
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

    user_id = context.user_data.get('user_id')
    # Send loading message to user
    loading_message = "Executing Swap, this might take a while..."
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text=loading_message)

    keyboard = [
        [InlineKeyboardButton("Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    public_key = context.user_data['public_key']
    private_key = context.user_data['private_key']
    amount_in = context.user_data['amount_in']
    token_in = context.user_data['token_in']
    token_out = context.user_data['token_out']
    
    token_in_symbol = context.user_data['token_in_symbol']
    token_out_symbol = context.user_data['token_out_symbol']

    try:
        receipt = await blockchain.web3_utils.swap_token(token_in, token_out, public_key, private_key, amount_in)
        tx_hash = receipt['transactionHash'].hex()
    
        amount_out = blockchain.web3_utils.parse_swap_receipt(receipt, token_out, public_key)
        await message.delete()
        text = f"""
                Swapped {amount_in} of {token_in_symbol} for {amount_out} of {token_out_symbol}!
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
                When Swapping {token_in_symbol} for {token_out_symbol}
                Tx Hash: {tx_hash}
                """
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text = text,
            reply_markup= reply_markup
        )
        return ROUTE

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
                CallbackQueryHandler(buy_tokens_confirmation, pattern="^buy_tokens_confirmation$"),
                CallbackQueryHandler(sell_tokens_confirmation, pattern="^sell_tokens_confirmation$"),
                CallbackQueryHandler(sell_tokens, pattern="^sell_tokens$"),
                CallbackQueryHandler(buy_tokens, pattern="^buy_tokens$"),
            },
            BUY_TOKENS: [MessageHandler(filters.TEXT, buy_tokens)],
            BUY_TOKENS_CONFIRMATION: [MessageHandler(filters.TEXT, buy_tokens_confirmation)],
            SELL_TOKENS_CONFIRMATION: [MessageHandler(filters.TEXT, sell_tokens_confirmation)],

        },
        fallbacks= [MessageHandler(filters.TEXT, unknown)]
    )
    app.add_handler(conversation_handler)

    app.run_polling()
    return


if __name__ == '__main__':
    main()
