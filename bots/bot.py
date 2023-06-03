import os
import sys
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler,CallbackContext,
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
    address = "0xCB182D3bec556974692bcF8504b433C30943AD93"
    # address = server.firebase_utils.get_user_address(user_id)

    balance = "0.0"
    transaction = "0"

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
    Address: {address}
    """

    await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=message, 
                parse_mode="markdown", 
                reply_markup=reply_markup
            )
    return ROUTE

def main():
    app = ApplicationBuilder().token(TELE_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.run_polling()
    return


if __name__ == '__main__':
    main()
