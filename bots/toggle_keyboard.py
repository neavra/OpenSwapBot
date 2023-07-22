import logging
import sys
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CallbackContext
)

sys.path.append("./")
import server.firebase_utils

load_dotenv()

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ROUTE, BUY_TOKENS_CONFIRMATION, SELL_TOKENS_CONFIRMATION, CUSTOM_AMOUNT, TRANSFER_TOKENS_CONFIRMATION, IMPORT_WALLET = range(6)
FEES = [3000]
WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6" # WETH GOERLI

async def emote(callback_data, emoji, states):
    for key, value in states.items():
        if key == callback_data:
            value = not value
            states[key] = value
        else:
            states[key] = False 
    
    for key,value in states.items():
        emoji[key] = '\u2705' if value else ''
    return emoji

async def toggle(update: Update, context: CallbackContext):
    custom_amount = context.user_data["custom_amount"]
    query= update.callback_query 
    await query.answer()
    callback_data = query.data

    amount_states = context.user_data["amount_states"]
    slippage_states = context.user_data["slippage_states"]
    type = context.user_data["type"]
    emoji = context.user_data["emoji"]

    if 'amount' in callback_data:
        emoji = await emote(callback_data, emoji, amount_states)
    else:    
        emoji = await emote(callback_data, emoji, slippage_states)
    context.user_data["emoji"] = emoji

    keyboard = await generate_keyboard(context)
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Deals with the case where custom amount is selected
    request_message = context.bot_data['request_message']
    if callback_data == "amount_custom":
        await request_message.delete()

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Please input a custom amount"
        )
        await query.edit_message_text(
            text = "Please choose:", 
            reply_markup=reply_markup
        )
        return CUSTOM_AMOUNT

    await query.edit_message_text(
        text = "Please choose:", 
        reply_markup=reply_markup
    )
    if type == "Sell":
        return SELL_TOKENS_CONFIRMATION
    elif type == "Buy":
        return BUY_TOKENS_CONFIRMATION

async def custom_amount(update: Update, context: CallbackContext):
    type = context.user_data["type"]
    keyboard_message = context.bot_data["keyboard_message"]
    slippage_states = context.user_data["slippage_states"]
    amount_states = context.user_data["amount_states"]
    emoji = context.user_data["emoji"]

    if update.callback_query:
        custom_amount = context.user_data["custom_amount"]
        query = update.callback_query
        await query.answer()
        callback_data = query.data
        emoji = await emote(callback_data, emoji, slippage_states)
        context.user_data["emoji"] = emoji
    if update.message:
        custom_amount = update.message.text
        context.user_data['custom_amount'] = custom_amount
        del amount_states['amount_custom']

        amount_states[f'amount_{custom_amount}'] = True
        keyboard = await generate_keyboard(context)
        reply_markup = InlineKeyboardMarkup(keyboard)

        await keyboard_message.edit_text(
            text = "Please choose:", 
            reply_markup=reply_markup
        )

        await context.bot.send_message( # This sends the prompt for a token address
            chat_id=update.effective_chat.id,
            text=f"Please enter the token you would like to buy, you can enter a symbol i.e. BTC or the contract address"
        )
        if type == "Sell":
            return SELL_TOKENS_CONFIRMATION
        elif type == "Buy":
            return BUY_TOKENS_CONFIRMATION

    keyboard = await generate_keyboard(context)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await keyboard_message.edit_text(
        text = "Please choose:", 
        reply_markup=reply_markup
    )
    
    return CUSTOM_AMOUNT

async def init_keyboard(type, context):
    user_id = context.user_data['user_id']
    wallet_count = server.firebase_utils.get_user(user_id)["walletCount"]

    context.user_data['wallet_count'] = wallet_count
    context.user_data['custom_amount'] = "--"
    context.user_data["type"] = type

    await init_keyboard_states(context)
    keyboard = await generate_keyboard(context)
    return keyboard

async def init_keyboard_states(context):
    wallet_count = context.user_data['wallet_count']

    amount_states = {
        'amount_0.001' : False,
        'amount_0.002' : False,
        'amount_custom': False,
    }
    slippage_states= {
        'slippage_auto' : True,
        'slippage_5' : False,
        'slippage_10' : False,
        'slippage_20' : False,
    }
    emoji = {
        'amount_0.001' : '',
        'amount_0.002' : '',
        'amount_custom': '',
        'slippage_auto' : '\u2705',
        'slippage_5' :  '',
        'slippage_10' :  '',
        'slippage_20' :  '',
    }
    wallet_states = {f'wallet_{i+1}': False for i in range(wallet_count)}

    context.user_data["amount_states"] = amount_states
    context.user_data["slippage_states"] = slippage_states
    context.user_data["wallet_states"] = wallet_states
    context.user_data["emoji"] = emoji

async def generate_keyboard(context):
    type = context.user_data["type"]
    custom_amount = context.user_data["custom_amount"]
    emoji = context.user_data["emoji"]
    wallet_states = context.user_data["wallet_states"]

    wallet_buttons = [
        InlineKeyboardButton(f'w{wallet_id[-1]}', callback_data=f"{wallet_id}")
        for wallet_id in wallet_states.keys()
    ]
    # keyboard += wallet_buttons
    keyboard = [
        [InlineKeyboardButton(f"Wallet", callback_data="empty")],
        []+wallet_buttons,
        [InlineKeyboardButton(f"{type} Amount", callback_data="empty")],
        [
            InlineKeyboardButton(f'0.001 {emoji["amount_0.001"]}', callback_data="amount_0.001"),
            InlineKeyboardButton(f'0.002 {emoji["amount_0.002"]}', callback_data="amount_0.002"),
            InlineKeyboardButton(f'Custom: {custom_amount} {emoji["amount_custom"]}', callback_data="amount_custom"),
        ],
        [InlineKeyboardButton("Slippage", callback_data="empty")],
        [
            InlineKeyboardButton(f'5% {emoji["slippage_5"]}', callback_data="slippage_5"),
            InlineKeyboardButton(f'10% {emoji["slippage_10"]}', callback_data="slippage_10"),
            InlineKeyboardButton(f'20% {emoji["slippage_20"]}', callback_data="slippage_20"),
            InlineKeyboardButton(f'Auto {emoji["slippage_auto"]}', callback_data="slippage_auto"),

        ],
        [InlineKeyboardButton("< Back", callback_data="start")]
    ]
    return keyboard