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
    user_id = update.message.from_user.id
    gas_fee, block_number = blockchain.web3_utils.get_ethereum_data()
    address = server.firebase_utils.get_user_address(user_id)

    if not address:
        # Onboard new user
        new_public_key, new_private_key = blockchain.web3_utils.create_wallet()
        server.firebase_utils.insert_user_address(user_id, new_public_key, new_private_key)
        address = server.firebase_utils.get_user_address(user_id)

    balance = blockchain.web3_utils.get_balance(address[0])
    transaction = blockchain.web3_utils.get_nonce(address[0])

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
    Address: {address[0]}
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
    user_id = 500148369

    await query.answer()
    # keyboard = [
    #     [InlineKeyboardButton("Back", callback_data="start")]
    # ]
    # reply_markup = InlineKeyboardMarkup(keyboard)
    address = server.firebase_utils.get_user_address(user_id)
    public_key = address[0]
    private_key = address[1]
    token = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984" # Uni token on Goerli
    tx_hash = await blockchain.web3_utils.buy_token(token, public_key, private_key, 0.0001)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"This is the buy tokens function: {tx_hash}",
        # reply_markup= reply_markup
    )
    return ROUTE

async def sell_tokens(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    # keyboard = [
    #     [InlineKeyboardButton("Back", callback_data="start")]
    # ]
    # reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text ="This is the sell tokens function",
        # reply_markup= reply_markup
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
