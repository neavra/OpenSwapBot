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
from toggle_keyboard import (toggle, custom_amount)
from buy import (buy_tokens_options, buy_tokens_confirmation, buy_tokens)
from sell import (sell_tokens_options, sell_tokens_confirmation, sell_tokens)
from transfer import (transfer_tokens_options, select_transfer_amount, select_transfer_address, transfer_tokens_confirmation, transfer_tokens)
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

ROUTE, BUY_TOKENS_CONFIRMATION, SELL_TOKENS_CONFIRMATION, CUSTOM_AMOUNT, TRANSFER_TOKENS_CONFIRMATION = range(5)
FEES = [3000]
WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6" # WETH GOERLI

TELE_TOKEN = os.getenv("TELE_TOKEN")

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
    context.user_data['public_key'] = public_key

    balance = blockchain.web3_utils.get_eth_balance(public_key)
    transaction = blockchain.web3_utils.get_nonce(public_key)

    keyboard = [
        [
            InlineKeyboardButton("Buy Tokens", callback_data="buy_tokens_options"),
            InlineKeyboardButton("Sell Tokens", callback_data="sell_tokens_options"),
        ],
        [
            InlineKeyboardButton("View Token Balances", callback_data="view_token_balances"),
            InlineKeyboardButton("List of Popular Tokens", callback_data="list_popular_tokens"),
        ],
        [
            InlineKeyboardButton("Transfer Tokens", callback_data="transfer_tokens_options")
        ]
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

async def view_token_balances(update: Update, context: CallbackContext):
    tokens = server.firebase_utils.get_tokens()
    text = "These are your balances:\n"
    public_key = context.user_data['public_key']
    for token in tokens:
        symbol = token["symbol"]
        balance = blockchain.web3_utils.get_balanceOf(token["address"], public_key)
        if balance != 0:
            text += f'Symbol: {symbol}\nBalance: {round(balance,5)}\n'
    # Handle no balances case
    if text == "These are your balances:\n":
        text = "You have no Available Balances!"

    keyboard = [
            [InlineKeyboardButton("< Back", callback_data="start")]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup= reply_markup
    )
    return ROUTE

async def list_popular_tokens(update: Update, context: CallbackContext):
    tokens = server.firebase_utils.get_tokens()
    text = "These are the tokens:\n"

    for token in tokens:
        symbol = token["symbol"]
        address = token["address"]
        text += f'Symbol: {symbol}\nAddress: {address}\n'

    keyboard = [
            [InlineKeyboardButton("< Back", callback_data="start")]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup= reply_markup
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


def main():
    app = ApplicationBuilder().token(TELE_TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start)
        ],
        states= {
            ROUTE: {
                CommandHandler('start', start),
                CallbackQueryHandler(start, pattern = "^start$"),
                CallbackQueryHandler(view_token_balances, pattern = "^view_token_balances$"),
                CallbackQueryHandler(list_popular_tokens, pattern = "^list_popular_tokens$"),
                CallbackQueryHandler(buy_tokens_options, pattern="^buy_tokens_options$"),
                CallbackQueryHandler(sell_tokens_options, pattern="^sell_tokens_options$"),
                CallbackQueryHandler(sell_tokens, pattern="^sell_tokens$"),
                CallbackQueryHandler(buy_tokens, pattern="^buy_tokens$"),
                CallbackQueryHandler(transfer_tokens_options, pattern = "^transfer_tokens_options$"),
                CallbackQueryHandler(select_transfer_amount, pattern="^select_transfer_amount.*"),
                CallbackQueryHandler(select_transfer_address, pattern = "^transfer_25%$"),
                CallbackQueryHandler(select_transfer_address, pattern = "^transfer_50%$"),
                CallbackQueryHandler(select_transfer_address, pattern = "^transfer_75%$"),
                CallbackQueryHandler(select_transfer_address, pattern = "^transfer_100%$"),
                CallbackQueryHandler(transfer_tokens, pattern = "^transfer_tokens$"),

            },
            BUY_TOKENS_CONFIRMATION: {
                CommandHandler('start', start),
                MessageHandler(filters.TEXT, buy_tokens_confirmation),
                CallbackQueryHandler(start, pattern = "^start$"),
                CallbackQueryHandler(toggle, pattern="^amount_0.001$"),
                CallbackQueryHandler(toggle, pattern="^amount_0.002$"),
                CallbackQueryHandler(toggle, pattern="^amount_custom$"),
                CallbackQueryHandler(toggle, pattern="^slippage_10$"),
                CallbackQueryHandler(toggle, pattern="^slippage_20$"),
                CallbackQueryHandler(toggle, pattern="^slippage_30$"),
            },
            SELL_TOKENS_CONFIRMATION: {
                CommandHandler('start', start),
                MessageHandler(filters.TEXT, sell_tokens_confirmation),
                CallbackQueryHandler(start, pattern = "^start$"),
                CallbackQueryHandler(toggle, pattern="^amount_0.001$"),
                CallbackQueryHandler(toggle, pattern="^amount_0.002$"),
                CallbackQueryHandler(toggle, pattern="^amount_custom$"),
                CallbackQueryHandler(toggle, pattern="^slippage_10$"),
                CallbackQueryHandler(toggle, pattern="^slippage_20$"),
                CallbackQueryHandler(toggle, pattern="^slippage_30$"),
            },
            CUSTOM_AMOUNT: {
                CommandHandler('start', start),
                MessageHandler(filters.TEXT, custom_amount),
                CallbackQueryHandler(custom_amount, pattern="^slippage_10$"),
                CallbackQueryHandler(custom_amount, pattern="^slippage_20$"),
                CallbackQueryHandler(custom_amount, pattern="^slippage_30$"),
            },
            TRANSFER_TOKENS_CONFIRMATION: {
                CommandHandler('start', start),
                MessageHandler(filters.TEXT, transfer_tokens_confirmation),
            }
        },
        fallbacks= [MessageHandler(filters.TEXT, unknown)]
    )
    app.add_handler(conversation_handler)

    app.run_polling()
    return

if __name__ == '__main__':
    main()
