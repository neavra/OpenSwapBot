from telegram import (
    Update
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler,CallbackContext,
)
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()

TELE_TOKEN = os.getenv("TELE_TOKEN")
NODE_PROVIDER_ENDPOINT = os.getenv("NODE_PROVIDER_ENDPOINT")

ROUTE, NEW_USER, NEW_USER_NAME, SHOW_QR = range(4)
# Function to handle the /start command
async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    gas_fee, block_number = get_ethereum_data()
    message = f"Current Gas Fees: {gas_fee} gwei\nCurrent Block Number: {block_number}"
    await context.bot.send_message(chat_id=chat_id, text=message)

# Function to retrieve Ethereum data
def get_ethereum_data():
    # Infura endpoint

    # Create a web3 instance using the Infura endpoint
    web3 = Web3(Web3.HTTPProvider(NODE_PROVIDER_ENDPOINT))

    # Get the current gas price
    gas_price = web3.eth.gas_price

    # Get the latest block number
    block_number = web3.eth.block_number

    # Convert gas price to gwei
    gas_fee = web3.from_wei(gas_price, 'ether')

    return gas_fee, block_number

def main():
    app = ApplicationBuilder().token(TELE_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.run_polling()
    return


if __name__ == '__main__':
    main()
