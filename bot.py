from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from web3 import Web3

# Function to handle the /start command
def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    gas_fee, block_number = get_ethereum_data()
    message = f"Current Gas Fees: {gas_fee} gwei\nCurrent Block Number: {block_number}"
    context.bot.send_message(chat_id=chat_id, text=message)

# Function to retrieve Ethereum data
def get_ethereum_data():
    # Infura endpoint
    infura_endpoint = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"  # Replace with your Infura project ID

    # Create a web3 instance using the Infura endpoint
    web3 = Web3(Web3.HTTPProvider(infura_endpoint))

    # Get the current gas price
    gas_price = web3.eth.gas_price

    # Get the latest block number
    block_number = web3.eth.block_number

    # Convert gas price to gwei
    gas_fee = web3.fromWei(gas_price, 'gwei')

    return gas_fee, block_number

def main():
    # Initialize the Telegram bot
    updater = Updater("YOUR_BOT_TOKEN")  # Replace with your own Telegram bot token
    dispatcher = updater.dispatcher

    # Register the /start command handler
    dispatcher.add_handler(CommandHandler("start", start))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
