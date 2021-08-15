import time
from typing import List
import telegram
from telegram.ext import (
    Updater, CallbackContext,
    CommandHandler, CallbackQueryHandler
)
from telegram import (
    Update, InlineKeyboardMarkup,
    InlineKeyboardButton
)
from api import send_notis, get_latest_block, get_balances
from utils import is_valid_address

from config import (
    BOT_TOKEN,
    ADD_WALLET, ALL_WALLET,
    DELETE_WALLET_BY_ID,
    CHECK_BALANCE
)
import db

import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher


def view_wallet(index, wallet):
    name = wallet[2]
    address = wallet[3]
    return f"""#{index + 1}\nName: *{name}*\nAddress: [{address}](https://etherscan.io/address/{address})"""


def view_wallets(wallets: List):
    if (len(wallets) == 0):
        return "You have 0 wallets.\n" \
            + f"Please use /{ADD_WALLET} to add wallet.\n" \
            + f"*Example*: /{ADD_WALLET} eth1 0x41667520bb471d18ea59591bc2de11bd82762241"

    return "Wallets\n\n" + "\n\n".join(view_wallet(i, wallet)
                                       for i, wallet in enumerate(wallets))


def get_wallets_markup(wallets, group_size=4):
    if (len(wallets) == 0):
        return None

    i = 0
    rows = []
    while i < len(wallets):
        row = [
            InlineKeyboardButton(
                text=str(i+j+1) + " " + "🗑️",
                callback_data="/" + DELETE_WALLET_BY_ID + " " + str(wallet[0])
            )
            for j, wallet in enumerate(wallets[i: i+group_size])
        ]
        rows.append(row)
        i = i + group_size

    return InlineKeyboardMarkup(inline_keyboard=rows)


def handle_start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    if (not db.check_user_exists(user_id)):
        db.add_user(user_id, username, first_name)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Welcom {first_name} to ETH bot.\n"
        "To add new wallet, use:\n/add <wallet_name> <address>\n."
        "To view all wallets, use:\n/all."
    )


def handle_balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    wallets = db.get_user_wallets(user_id)
    addresses = [wallet[3] for wallet in wallets]

    if (len(wallets) == 0):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=view_wallets(wallets),
            parse_mode="MARKDOWN"
        )
        return

    try:
        balancesDict = get_balances(addresses)
        message = "*Balance*"
        for id, wallet in enumerate(wallets):
            name = wallet[2]
            address = wallet[3]
            balance = float(balancesDict.get(address)) / 10**18
            message += f"\n#{id} \nName: [{name}](https://etherscan.io/address/{address}) \nBalance: *{balance}* ETH \n"

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            parse_mode="MARKDOWN",
            disable_web_page_preview=True
        )

    except Exception as ex:
        logger.error("When get balances of addresses: " +
                     str(addresses) + " Error: " + str(ex))
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Error while get balance from Etherscan"
        )


def handle_get_wallets(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    wallets = db.get_user_wallets(user_id)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=view_wallets(wallets),
        reply_markup=get_wallets_markup(wallets),
        parse_mode="MARKDOWN",
        disable_web_page_preview=True
    )


def handle_new_wallet(update: Update, context: CallbackContext):
    args = context.args
    command = "/" + ADD_WALLET
    user_id = update.effective_user.id

    if (len(args) != 2):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"You need to provide *wallet name* and *address* after {command}\n"
            + f"*Example*: /{ADD_WALLET} eth1 0x41667520bb471d18ea59591bc2de11bd82762241",
            parse_mode=telegram.ParseMode.MARKDOWN_V2
        )
    else:
        wallet_name = args[0]
        address = args[1]
        if (not is_valid_address(address)):
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"The wallet address <b>{address}</b> is INVALID",
                parse_mode="HTML"
            )
        elif (db.check_wallet_exists(user_id=user_id, address=address)):
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"The wallet address <b>{address}</b> already exists",
                parse_mode="HTML"
            )
        else:
            try:
                latest_block = get_latest_block()
                db.add_wallet(user_id, wallet_name, address, latest_block)
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Add wallet {wallet_name} successfully!\n"
                    + f"Please use /{ALL_WALLET} to list your wallets."
                )
            except Exception as ex:
                logger.error(str(ex))
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"ERROR: Can not add wallet {address}"
                )


def handle_inline_delete_wallet(update: Update, context: CallbackContext):
    data = update.callback_query.data
    wallet_id = int(data.split()[-1])

    user_id = update.effective_user.id

    if (db.check_wallet_id_and_user_exists(wallet_id, user_id)):
        db.delete_wallet(wallet_id)
        wallets = db.get_user_wallets(user_id)
        update.callback_query.edit_message_text(
            text=view_wallets(wallets),
            reply_markup=get_wallets_markup(wallets),
            parse_mode="MARKDOWN",
            disable_web_page_preview=True
        )
    else:
        update.callback_query.edit_message_reply_markup(reply_markup=None)


def handle_error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


dispatcher.add_handler(CommandHandler("start", handle_start))
dispatcher.add_handler(CommandHandler(CHECK_BALANCE, handle_balance))
dispatcher.add_handler(CommandHandler(ALL_WALLET, handle_get_wallets))
dispatcher.add_handler(CommandHandler(ADD_WALLET, handle_new_wallet))
dispatcher.add_handler(CallbackQueryHandler(
    handle_inline_delete_wallet, pattern="/" + DELETE_WALLET_BY_ID + "*"))
dispatcher.add_error_handler(handle_error)


bot = updater.bot


updater.start_polling()


try:
    latest_block = get_latest_block()
    db.update_all_latest_block(latest_block)
    logger.info("Update all latest block to " + str(latest_block))
except Exception as ex:
    logger.error(
        "When start: Cant not update latest block, Exception: " + str(ex))

while True:
    send_notis(bot)
