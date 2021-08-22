from typing import Dict, List
import logging
import time
import traceback

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


def __send_noti(bot: Bot, user_id, name, address, transaction: Dict, transfers: List[Dict]):
    text = ""
    value = float(transaction.get("value")) / 10**18
    from_ = transaction.get("from")
    to_ = transaction.get("to")
    hash = transaction.get("hash")
    blockNumber = int(transaction.get("blockNumber"))

    input_code = transaction.get("input")

    bonus_message = ""
    for event in transfers:
        token_hash = event.get("hash")
        if (token_hash == hash):
            token_from = event.get("from")
            token_to = event.get("to")
            token_symbol = event.get("tokenSymbol")
            token_value = float(event.get("value")) / \
                10**(int(event.get("tokenDecimal")))
            if (str.lower(token_from) == str.lower(address)):
                bonus_message += f"➖*{token_value} {token_symbol}* \nFROM [{name}](https://etherscan.io/address/{token_from}) \n\nTO [{token_to}](https://etherscan.io/address/{token_to}) \t[[View in Etherscan](https://etherscan.io/tx/{token_hash})]"
            elif (str.lower(token_to) == str.lower(address)):
                bonus_message += f"➕*{token_value} {token_symbol}* \nFROM [{token_from}](https://etherscan.io/address/{token_from}) \n\nTO [{name}](https://etherscan.io/address/{token_to}) \t[[View in Etherscan](https://etherscan.io/tx/{token_hash})]"
            else:
                bonus_message += f"➕*{token_value} {token_symbol}* \nFROM [{token_from}](https://etherscan.io/address/{token_from}) \n\nTO [{token_to}](https://etherscan.io/address/{token_to}) \t[[View in Etherscan](https://etherscan.io/tx/{token_hash})]"
            bonus_message += "\n\n"

    if (str.lower(from_) == str.lower(address)):
        text = f"➖*{value} ETH* \nFROM [{name}](https://etherscan.io/address/{from_}) \n\nTO [{to_}](https://etherscan.io/address/{to_}) \t[[View in Etherscan](https://etherscan.io/tx/{hash})]"
    else:
        text = f"➕*{value} ETH* \nFROM [{from_}](https://etherscan.io/address/{from_}) \n\nTO [{name}](https://etherscan.io/address/{to_}) \t[[View in Etherscan](https://etherscan.io/tx/{hash})]"

    db.update_latest_block(user_id, address, blockNumber)

    bot.send_message(
        chat_id=user_id,
        text=text + "\n\n" + bonus_message,
        parse_mode="MARKDOWN",
        disable_web_page_preview=True
    )


def send_notis(bot: Bot, wallets):
    try:
        addresses = [wallet[3] for wallet in wallets]
        t0 = time.time()
        balancesDict = get_balances(addresses)
        logger.info(str(time.time() - t0) + " s to get balance of " +
                    str(len(addresses)) + " addresses")

        for wallet in wallets:
            request_count = 0
            begin_each_wallet_time = time.time()
            try:
                user_id = wallet[1]
                name = wallet[2]
                address = wallet[3]
                latest_block = wallet[4]
                balance = wallet[5]
                new_balance = balancesDict.get(str.lower(address))

                if (new_balance is None):
                    logger.info(name + ": MUST check balance AGAIN")

                    request_count += 1
                    new_balance = get_balance(address)
                    if (new_balance is None):
                        logger.error(name + ": Can NOT get balance AGAIN")
                        continue

                if (str.lower(balance) == str.lower(new_balance)):
                    logger.info(name + ": not change balance " + new_balance)

                else:
                    logger.info(name + ": new balance " +
                                balance + " => " + new_balance)

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

                db.update_balance(user_id, address, new_balance)
                logger.info(name + ": Update balance to " + str(new_balance))

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


def test():
    res = eth.get_erc20_token_transfer_events_by_address(
        address="0xc08a16ffDEfAfd04Cb4E56138507b70E6dB2F679", startblock=13036050, endblock=13036150, sort="asc")
    print(res)
