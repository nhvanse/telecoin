from typing import Dict, List
import logging
import time
import traceback

import etherscan

from config import ETHERSCAN_TOKEN, MIN_DURATION_BTW_REQUESTS
import db

from etherscan import Etherscan
from telegram import Bot


logger = logging.getLogger(__name__)

eth = Etherscan(ETHERSCAN_TOKEN)


def get_latest_block():
    # res = eth.get_normal_txs_by_address_paginated(address, 1, 1, None, None, "desc")
    res = eth.get_block_number_by_timestamp(int(time.time()), "before")

    return int(res)


def get_balance(address):
    res = eth.get_eth_balance(address)
    return res


def get_balances(addresses: List[str]) -> Dict[str, str]:
    res = eth.get_eth_balance_multiple(addresses)

    return {item["account"]: item["balance"] for item in res}

def format_address(address):

    return address[:6] + ".." + address[-6:]

def __send_noti(bot: Bot, user_id, name, address, transaction: Dict, transfers: List[Dict]):
    text = ""
    value = float(transaction.get("value")) / 10**18
    from_ = transaction.get("from")
    to_ = transaction.get("to")
    hash = transaction.get("hash")
    blockNumber = int(transaction.get("blockNumber"))

    etherscan_view = f"[[View in Etherscan](https://etherscan.io/tx/{hash})]"

    if (str.lower(from_) == str.lower(address)):
        text = f"[{name}](https://etherscan.io/address/{from_}) \n➖*{value} ETH* \nTO [{format_address(to_)}](https://etherscan.io/address/{to_})"
    else:
        text = f"[{name}](https://etherscan.io/address/{to_})   \n➕*{value} ETH* \nFROM [{format_address(from_)}](https://etherscan.io/address/{from_})"

    

    db.update_latest_block(user_id, address, blockNumber)

    bot.send_message(
        chat_id=user_id,
        text=text + " " + etherscan_view,
        parse_mode="MARKDOWN",
        disable_web_page_preview=True
    )


    bonus_message = ""
    for event in transfers:
        token_hash = event.get("hash")
        if (token_hash == hash):
            token_from = event.get("from")
            token_to = event.get("to")
            token_symbol = event.get("tokenSymbol")
            token_name = event.get("tokenName")
            contract_address = event.get("contractAddress")
            token_value = float(event.get("value")) / \
                10**(int(event.get("tokenDecimal")))


            if (str.lower(token_from) == str.lower(address)):
                bonus_message = f"[{name}](https://etherscan.io/address/{token_from})  \n➖*{token_value} {token_symbol}*([{token_name}](https://etherscan.io/address/{contract_address})) \nTO [{format_address(token_to)}](https://etherscan.io/address/{token_to}) "
            elif (str.lower(token_to) == str.lower(address)):
                bonus_message = f"[{name}](https://etherscan.io/address/{token_to})    \n➕*{token_value} {token_symbol}*([{token_name}](https://etherscan.io/address/{contract_address})) \nFROM [{format_address(token_from)}](https://etherscan.io/address/{token_from})"
            else:
                bonus_message = f"[{name}](https://etherscan.io/address/{address})     \nTransfer *{token_value} {token_symbol}* \nFROM [{format_address(token_from)}](https://etherscan.io/address/{token_from}) \nTO [{format_address(token_to)}](https://etherscan.io/address/{token_to}) "
            
            bot.send_message(
                chat_id=user_id,
                text=bonus_message + " " + etherscan_view,
                parse_mode="MARKDOWN",
                disable_web_page_preview=True
            )


def send_notis(bot: Bot, wallets):
    try:
        # addresses = [wallet[3] for wallet in wallets]
        # t0 = time.time()
        # balancesDict = get_balances(addresses)
        # logger.info(str(time.time() - t0) + " s to get balance of " +
        #             str(len(addresses)) + " addresses")

        for wallet in wallets:
            request_count = 0
            begin_each_wallet_time = time.time()
            try:
                user_id = wallet[1]
                name = wallet[2]
                address = wallet[3]
                latest_block = wallet[4]
                balance = wallet[5]
                # new_balance = balancesDict.get(str.lower(address))

                # if (new_balance is None):
                #     logger.info(name + ": MUST check balance AGAIN")

                #     request_count += 1
                #     new_balance = get_balance(address)
                #     if (new_balance is None):
                #         logger.error(name + ": Can NOT get balance AGAIN")
                #         continue

                # if (str.lower(balance) == str.lower(new_balance)):
                #     logger.info(name + ": not change balance " + new_balance)

                # else:

                if (True):

                    #TODO
                    # logger.info(name + ": new balance " +
                    #             balance + " => " + new_balance)

                    timeBeginGetTxs = time.time()
                    request_count += 1
                    res = eth.get_normal_txs_by_address(
                        address, latest_block + 1, None, "asc")

                    logger.info(name + ": " + str(res))
                    logger.info(name + ": get " + str(len(res)) +
                                " txs " + str(time.time() - timeBeginGetTxs) + " s")

                    try:
                        timeBeginGetTransfers = time.time()
                        request_count += 1
                        res2 = eth.get_erc20_token_transfer_events_by_address(
                            address=address, startblock=latest_block+1, endblock=None, sort="asc")

                        logger.info(name + "transfer: " + str(res2))
                        logger.info(name + ": get " + str(len(res2)) +
                                    " transfers " + str(time.time() - timeBeginGetTransfers) + " s")
                    except Exception as e:
                        logger.error(
                            name + ": Can NOT get ERC20 token. Ex:" + str(e))
                        res2 = []

                    t0 = time.time()
                    for transaction in res:
                        try:
                            __send_noti(bot, user_id, name,
                                        address, transaction, res2)

                        except Exception as e:

                            logger.error(
                                name + ": Can not send new transaction " + str(transaction.get("hash")) + "\tException: " + str(ex))

                    logger.info(name + ": " + str(time.time() - t0) + " s to send all " +
                                str(len(res)) + " telegram messages")

            except Exception as ex:
                traceback.print_exc()
                logger.error(str(wallet[2]) + ": " + str(ex))

                # db.update_balance(user_id, address, new_balance)
                # logger.info(name + ": Update balance to " + str(new_balance))

            duration = time.time() - begin_each_wallet_time
            sleep_duration = 0 if duration >= request_count else request_count - duration
            time.sleep(sleep_duration)

        time.sleep(1)

    except Exception as ex:
        logger.error(str(ex))


def send_all_notis(bot: Bot):
    wallets = db.get_all_wallets()

    i = 0
    while i < len(wallets):
        endId = i + 19
        sub_wallets = wallets[i: endId]
        send_notis(bot, sub_wallets)
        i = endId


