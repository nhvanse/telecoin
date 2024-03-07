# Telecoin
A chat bot uses Telegram api and Etherscan to register ETH wallet balance change notifications.

This is a small project for personal use only.
## Setup
- Go [Telegram Bot Father](https://t.me/BotFather) to create a new bot, then copy the bot token and update the value in config.py
- Go [Etherscan](https://etherscan.io) to register token, copy it and update the value in config.py
- Run `docker-compose up`
## Result
- Add a new wallet: /new {wallet_name} {wallet_address}
- Manage current wallets: /all
- Receive notifications when the wallet balance change
<img width="984" alt="image" src="https://github.com/nhvanse/telecoin/assets/35824966/ac83cd9e-961f-4088-957c-c86f4e2c7f94">


