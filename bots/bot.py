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

ROUTE = range(1)
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
        [InlineKeyboardButton("Buy Tokens", callback_data="buy_tokens_confirmation"),InlineKeyboardButton("Sell Tokens", callback_data="sell_tokens_options")]
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
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I did not understand that command",
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
    return ROUTE

async def buy_tokens_confirmation(update: Update, context: CallbackContext):
    context.user_data['amount_in'] = 0.0001
    context.user_data['token_in'] = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
    context.user_data['token_out'] = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"

    amount_in = context.user_data['amount_in']
    token_in = context.user_data['token_in']
    token_out = context.user_data['token_out']
    path = [token_in, token_out]
    fees = [3000]
    path_bytes = blockchain.web3_utils.encode_path(path, fees, True)

    amount_out = await blockchain.web3_utils.get_swap_quote(path_bytes, amount_in)

    token_in_symbol = blockchain.web3_utils.get_symbol(token_in)
    token_out_symbol = blockchain.web3_utils.get_symbol(token_out)

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

async def buy_tokens(update: Update, context: CallbackContext):
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

    address = server.firebase_utils.get_user_address(user_id)
    public_key = address[0]
    private_key = address[1]
    amount_in = context.user_data['amount_in']
    token_in = context.user_data['token_in']
    token_out = context.user_data['token_out']


    validation_result = blockchain.web3_utils.validate_params(token_in, token_out, public_key, amount_in)

    if validation_result:
        await message.delete()
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"{str(validation_result)}",
        reply_markup= reply_markup
        )
        return
    
    token_in_symbol = blockchain.web3_utils.get_symbol(token_in)
    token_out_symbol = blockchain.web3_utils.get_symbol(token_out)

    receipt = await blockchain.web3_utils.swap_token(token_in, token_out, public_key, private_key, amount_in)
    tx_hash = receipt['transactionHash'].hex()
   
    amount_out = blockchain.web3_utils.parse_swap_receipt(receipt, token_out, public_key)
    await message.delete()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"Swapped {amount_in} of {token_in_symbol} for {amount_out} of {token_out_symbol}!\n Tx hash: {tx_hash}",
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
        text="Please enter a contract address"
    )
    return ROUTE

async def sell_tokens(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text ="This is the sell tokens function",
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
                CallbackQueryHandler(sell_tokens, pattern="^sell_tokens$"),
                CallbackQueryHandler(buy_tokens, pattern="^buy_tokens$"),
            }
        },
        fallbacks= [MessageHandler(filters.TEXT, unknown)]
    )
    app.add_handler(conversation_handler)

    app.run_polling()
    return


if __name__ == '__main__':
    main()
