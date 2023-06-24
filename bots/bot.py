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

ROUTE, BUY_TOKENS_CONFIRMATION, SELL_TOKENS_CONFIRMATION = range(3)
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
            [InlineKeyboardButton("< Back", callback_data="start")]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I did not understand that command",
        reply_markup= reply_markup
    )

async def buy_tokens_options(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Buy Amount", callback_data="")],
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2"),
        ],
        [InlineKeyboardButton("Slippage", callback_data="")],
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
    
    path = [token_in, token_out]
    path_bytes = blockchain.web3_utils.encode_path(path, fees, True)

    context.user_data['path_bytes'] = path_bytes

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

    user_id = context.user_data.get('user_id')
    # Send loading message to user
    loading_message = "Executing Swap, this might take a while..."
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text=loading_message)

    keyboard = [
        [InlineKeyboardButton("< Back", callback_data="start")]
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
    keyboard = [
        [InlineKeyboardButton("sell Amount", callback_data="start")],
        [
            InlineKeyboardButton("0.001", callback_data="toggle_0.001"),
            InlineKeyboardButton("0.002", callback_data="toggle_0.002"),
        ],
        [InlineKeyboardButton("Slippage", callback_data="start")],
        [
            InlineKeyboardButton("10%", callback_data="slippage_10"),
            InlineKeyboardButton("20%", callback_data="slippage_20"),
            InlineKeyboardButton("30%", callback_data="slippage_30"),

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
    user_id = context.user_data.get('user_id')
    token_in = update.message.text

    address = server.firebase_utils.get_user_address(user_id)
    public_key = address[0]
    private_key = address[1]
    toggle_states = context.user_data["toggle_states"]
    slippage_states = context.user_data["slippage_states"]

    for key, value in toggle_states.items():
        if value == True:
            amount_in = float(key[-5:])

    #checks if an amount was selected
    if all(value is False for value in toggle_states.values()) or all(value is False for value in slippage_states.values()):
        keyboard = [
            [InlineKeyboardButton("< Back", callback_data="sell_tokens_options")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text =f"Please select an amount and slippage",
        reply_markup= reply_markup
        )
        return ROUTE


            
    context.user_data['amount_in'] = amount_in
    context.user_data['token_in'] = token_in
    context.user_data['token_out'] = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6" # WETH
    context.user_data['public_key'] = public_key
    context.user_data['private_key'] = private_key

    amount_in = context.user_data['amount_in']
    token_in = context.user_data['token_in']
    token_out = context.user_data['token_out']

    token_in_symbol = blockchain.web3_utils.get_symbol(token_in)
    token_out_symbol = blockchain.web3_utils.get_symbol(token_out)
    fees = [3000]

    context.user_data['token_in_symbol'] = token_in_symbol
    context.user_data['token_out_symbol'] = token_out_symbol
    context.user_data['fees'] = fees

    
    path = [token_in, token_out]
    path_bytes = blockchain.web3_utils.encode_path(path, fees, True)

    context.user_data['path_bytes'] = path_bytes

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

    user_id = context.user_data.get('user_id')
    # Send loading message to user
    loading_message = "Executing Swap, this might take a while..."
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text=loading_message)

    keyboard = [
        [InlineKeyboardButton("< Back", callback_data="start")]
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

async def toggle(update: Update, context: CallbackContext):
    query= update.callback_query 
    await query.answer()
    callback_data = query.data
    category = callback_data[:3]

    toggle_states = context.user_data["toggle_states"]
    slippage_states = context.user_data["slippage_states"]
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
        [InlineKeyboardButton("Sell Amount", callback_data="start")],
        [
            InlineKeyboardButton(f'0.001 {emoji["toggle_0.001"]}', callback_data="toggle_0.001"),
            InlineKeyboardButton(f'0.002 {emoji["toggle_0.002"]}', callback_data="toggle_0.002"),
        ],
        [InlineKeyboardButton("Slippage", callback_data="start")],
        [
            InlineKeyboardButton(f'10% {emoji["slippage_10"]}', callback_data="slippage_10"),
            InlineKeyboardButton(f'20% {emoji["slippage_20"]}', callback_data="slippage_20"),
            InlineKeyboardButton(f'30% {emoji["slippage_30"]}', callback_data="slippage_30"),

        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text = "Please choose:", 
        reply_markup=reply_markup)
    return SELL_TOKENS_CONFIRMATION

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
            BUY_TOKENS_CONFIRMATION: [MessageHandler(filters.TEXT, buy_tokens_confirmation)],
            SELL_TOKENS_CONFIRMATION: {
                MessageHandler(filters.TEXT, sell_tokens_confirmation),
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
