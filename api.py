from typing import Dict, List
import logging
import time

from config import ETHERSCAN_TOKEN
import db

from etherscan import Etherscan
from telegram import Bot

logger = logging.getLogger(__name__)

eth = Etherscan(ETHERSCAN_TOKEN)


def get_latest_block():
    # res = eth.get_normal_txs_by_address_paginated(address, 1, 1, None, None, "desc")
    res = eth.get_block_number_by_timestamp(int(time.time()), "before")

    return int(res)

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


def send_notis(bot: Bot):
    try:
        wallets = db.get_all_wallets()

        for wallet in wallets:
            beginTime = time.time()
            try:
                user_id = wallet[1]
                name = wallet[2]
                address = wallet[3]
                latest_block = wallet[4]

                res = eth.get_normal_txs_by_address(
                    address, latest_block + 1, None, "asc")

                for transaction in res:
                    try:
                        __send_noti(bot, user_id, name, address, transaction)

                    except Exception as e:
                        
                        logger.error(
                            "Can not send new transactions " + str(transaction) + " Exception: " + str(ex))

                
            except Exception as ex:
                logger.error(f"When get txs by address {address} : " + str(ex))

            endTime = time.time()
            duration = endTime - beginTime

            sleepDuration = 0 if duration >= 1 else 1 - duration
            time.sleep(sleepDuration)
    except Exception as ex:
        logger.error(str(ex))
