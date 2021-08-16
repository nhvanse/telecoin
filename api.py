from typing import Dict, List
import logging
import time

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


def send_notis(bot: Bot):
    wallets = db.get_all_wallets()

    i = 0
    while i < len(wallets):
        endId = i + 19
        sub_wallets = wallets[i: endId]
        send_notis2(bot, sub_wallets)
        i = endId
    
def send_notis2(bot: Bot, wallets):
    try:
        addresses = [wallet[3] for wallet in wallets]
        t0 = time.time()
        balancesDict = get_balances(addresses)
        logger.info(str(time.time() - t0) + " s to get balance of " + str(len(addresses)) + " addresses")
        for wallet in wallets:
            beginTime = time.time()
            try:
                user_id = wallet[1]
                name = wallet[2]
                address = wallet[3]
                latest_block = wallet[4]
                balance = wallet[5]
                new_balance = balancesDict.get(str.lower(address))

                if (str.lower(balance) == str.lower(new_balance)):
                    logger.info(name + " not change balance " + new_balance)

                else:
                    logger.info("old: " + balance + " new: "+ new_balance)
                    timeBeginGetTxs = time.time()
                    res = eth.get_normal_txs_by_address(
                        address, latest_block + 1, None, "asc")
                
                    logger.info(str(time.time() - timeBeginGetTxs) + " s to get txs from  " + str(name))



                    logger.info(f"Get {len(res)} txs from wallet {name}")
                    db.update_balance(user_id, address, new_balance)
                    logger.info(name + ": Update balance to " + new_balance)
                    
                    t0 = time.time()
                    for transaction in res:
                        try:
                            __send_noti(bot, user_id, name, address, transaction)

                        except Exception as e:
                            
                            logger.error(
                                "Can not send new transactions " + str(transaction) + " Exception: " + str(ex))
                    logger.info(str(time.time() - t0) + " s to send " + str(len(res)) + " notis from " + str(name))
                    
            except Exception as ex:
                # logger.error(f"When get txs by address {address} : " + str(ex))
                logger.info(str(time.time() - beginTime) + " s: " + str(wallet[2]) + " " + str(ex))
                pass

            # endTime = time.time()
            # duration = endTime - beginTime

            # sleepDuration = 0 if duration >= 2*MIN_DURATION_BTW_REQUESTS else 2*MIN_DURATION_BTW_REQUESTS - duration
            # logger.info("duration " + str(duration))
            # logger.info("sleep " + str(sleepDuration))
            # time.sleep(sleepDuration)
    except Exception as ex:
        logger.error(str(ex))

def send_notis1(bot: Bot):
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
                
                logger.info(f"Get {len(res)} txs from address {address}")

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

            sleepDuration = 0 if duration >= MIN_DURATION_BTW_REQUESTS else MIN_DURATION_BTW_REQUESTS - duration
            time.sleep(sleepDuration)
    except Exception as ex:
        logger.error(str(ex))

# a = get_balances(
#     [
#         "0xBF4406b711F473dACD5618EcA2f559318A4e6Bfe",
#         "0x5A0b54D5dc17e0AadC383d2db43B0a0D3E029c4c",
#         "0x8a369e1ffdDD7157fFb69F440a2B24B769Bd21D1",
#         "0x5094819279C67a77342705Cf420CA07eE0e5e76b",
#         "0xdac17f958d2ee523a2206206994597c13d831ec7",
#         "0xfef5c1cd156902c3232d203c35d7434c47f55b27",
#         "0xfef5c1cd156902c3232d203c35d7434c47f55b29",
#         "0x182a468828eece7515322a093483879ef4fb8ee2",
#         "0x994fb17ba1c18770269adf0dfeed3b5f35cd8251",
#         "0x8f546fdb1d8c069f091a6b99fead4deaade7f951",
#         "0xBF4406b711F473dACD5618EcA2f559318A4e6Bfa",
#         "0x5A0b54D5dc17e0AadC383d2db43B0a0D3E029c4e",
#         "0x8a369e1ffdDD7157fFb69F440a2B24B769Bd21D4",
#         "0x5094819279C67a77342705Cf420CA07eE0e5e76c",
#         "0xdac17f958d2ee523a2206206994597c13d831ec8",
#         "0xfef5c1cd156902c3232d203c35d7434c47f55b29",
#         "0xfef5c1cd156902c3232d203c35d7434c47f55b28",
#         "0x182a468828eece7515322a093483879ef4fb8ee7",
#         "0x994fb17ba1c18770269adf0dfeed3b5f35cd825f"
#         ]
# )
# print(a)