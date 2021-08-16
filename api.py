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


def __send_noti(bot: Bot, user_id, name, address, transaction: Dict):
    text = ""
    value = float(transaction.get("value")) / 10**18
    from_ = transaction.get("from")
    to_ = transaction.get("to")
    hash = transaction.get("hash")
    blockNumber = int(transaction.get("blockNumber"))

    if (str.lower(from_) == str.lower(address)):
        text = f"➖*{value} ETH* \nFROM [{name}](https://etherscan.io/address/{from_}) \n\nTO [{to_}](https://etherscan.io/address/{to_}) \t[[View in Etherscan](https://etherscan.io/tx/{hash})]"
    else:
        text = f"➕*{value} ETH* \nFROM [{from_}](https://etherscan.io/address/{from_}) \n\nTO [{name}](https://etherscan.io/address/{to_}) \t[[View in Etherscan](https://etherscan.io/tx/{hash})]"

    bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="MARKDOWN",
        disable_web_page_preview=True
    )

    db.update_latest_block(user_id, address, blockNumber)


def send_notis(bot: Bot, wallets):
    try:
        addresses = [wallet[3] for wallet in wallets]
        t0 = time.time()
        balancesDict = get_balances(addresses)
        logger.info(str(time.time() - t0) + " s to get balance of " +
                    str(len(addresses)) + " addresses")
        
        for wallet in wallets:
            try:
                user_id = wallet[1]
                name = wallet[2]
                address = wallet[3]
                latest_block = wallet[4]
                balance = wallet[5]
                new_balance = balancesDict.get(str.lower(address))

                if (new_balance is None):
                    logger.info(name + ": MUST check balance AGAIN")
                    new_balance = get_balance(address)
                    if (new_balance is None):
                        logger.error(name + ": Can NOT get balance")
                        continue

                if (str.lower(balance) == str.lower(new_balance)):
                    logger.info(name + ": not change balance " + new_balance)

                else:
                    logger.info(name + ": new balance " + balance + " => " + new_balance)
                    
                    timeBeginGetTxs = time.time()
                    res = eth.get_normal_txs_by_address(
                        address, latest_block + 1, None, "asc")
                    
                    logger.info(name + ": get " + str(len(res)) + " txs " + str(time.time() - timeBeginGetTxs) + " s")

                    

                    t0 = time.time()
                    for transaction in res:
                        try:
                            __send_noti(bot, user_id, name,
                                        address, transaction)

                        except Exception as e:

                            logger.error(
                                name + ": Can not send new transaction " + str(transaction.get("hash")) + "\tException: " + str(ex))
                    
                    time.sleep(0.5)
                    logger.info(name + ": " + str(time.time() - t0) + " s to send all " +
                                str(len(res)) + " telegram messages")

            except Exception as ex:
                traceback.print_exc()
                logger.error(str(wallet[2]) + ": " + str(ex))

                db.update_balance(user_id, address, new_balance)
                logger.info(name + ": Update balance to " + str(new_balance))
        
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

