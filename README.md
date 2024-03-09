# Telecoin
A chat bot uses Telegram api and Etherscan to register ETH wallet balance change notifications.

This is a small project for personal use only.
## Setup
- Go [Telegram Bot Father](https://t.me/BotFather) to create a new bot, then copy the bot token and update the value in config.py
- Go [Etherscan](https://etherscan.io) to register API token, copy it and update the value in config.py
- Run `docker-compose up`
## Result
- Add a new wallet: /new {wallet_name} {wallet_address}
- List all wallets: /all
- Delete a wallet: Click on the trash icon
- Check balance: /balance
- Receive notifications when the wallet balance change
1. <img width="1348" alt="image" src="https://github.com/nhvanse/telecoin/assets/35824966/4e69dab9-f151-4642-a616-78e513a01085">

2. <img width="1346" alt="image" src="https://github.com/nhvanse/telecoin/assets/35824966/a4a5c1e3-659b-41e5-894f-dc91b7931b91">




