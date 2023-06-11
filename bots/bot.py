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
    public_key = address[0]

    if not address:
        # Onboard new user
        new_public_key, new_private_key = blockchain.web3_utils.create_wallet()
        server.firebase_utils.insert_user_address(user_id, new_public_key, new_private_key)
        address = server.firebase_utils.get_user_address(user_id)

    balance = blockchain.web3_utils.get_balance(public_key)
    transaction = blockchain.web3_utils.get_nonce(public_key)

    keyboard = [
        [InlineKeyboardButton("Buy Tokens", callback_data="buy_tokens"),InlineKeyboardButton("Sell Tokens", callback_data="sell_tokens")]
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

async def buy_tokens(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = context.user_data.get('user_id')

    keyboard = [
        [InlineKeyboardButton("Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    address = server.firebase_utils.get_user_address(user_id)
    public_key = address[0]
    private_key = address[1]
    token_out = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6" # WETH token on Goerli
    token_in = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984" # Uni token on Goerli

    token_in_symbol = blockchain.web3_utils.get_symbol(token_in)
    token_out_symbol = blockchain.web3_utils.get_symbol(token_out)
    amount_in = 0.0001
    receipt = await blockchain.web3_utils.swap_token(token_in, token_out, public_key, private_key, amount_in)
    tx_hash = receipt['transactionHash'].hex()
   
    amount_out = blockchain.web3_utils.parse_swap_receipt(receipt, token_out, public_key)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"Swapped {amount_in} of {token_in_symbol} for {amount_out} of {token_out_symbol}!\n Tx hash: {tx_hash}",
        reply_markup= reply_markup
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
                CallbackQueryHandler(buy_tokens, pattern="^buy_tokens$"),
                CallbackQueryHandler(sell_tokens, pattern="^sell_tokens$")
            }
        },
        fallbacks= [MessageHandler(filters.TEXT, unknown)]
    )
    app.add_handler(conversation_handler)

    app.run_polling()
    return


if __name__ == '__main__':
    main()
