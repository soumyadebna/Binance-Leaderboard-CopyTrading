# Binance-Leaderboard-CopyTrading

Binance-Leaderboard-CopyTrading allows users to automate their trading strategies by copying the trades from Binance's top traders directly into their Bybit account. With an integrated Telegram bot and Coinable Commerce, monetizing the tool becomes straightforward!

## Features

- Trade Scraping: Automatically scrape trades from the Binance leaderboard.
- Bybit Integration: Replicate trades directly on your Bybit account.
- Telegram Bot: Seamless interaction and configuration using a dedicated bot.
- Coinbase Commerce Integration: Planning to sell? Integrate with Coinable Commerce with ease.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- A Bybit account
- Binance account (optional for viewing leaderboard)
- Telegram account

### Installation

1. Clone the repository:
    ```
    git clone https://github.com/your_username/Binance-Leaderboard-CopyTrading.git
    ```
2. Navigate to the project directory and install dependencies:
    ```
    cd Binance-Leaderboard-CopyTrading
    pip install -r requirements.txt
    ```
3. Environment Variables: Create a `.env` file in the root directory and populate with the following keys:
    ```
    API_KEY=your_coinbase_commerce_api_key
    TOKEN=your_telegram_bot_token
    TRADER_1_UUID=encrypted_uuid_of_trader_1
    TRADER_2_UUID=encrypted_uuid_of_trader_2
    TRADER_3_UUID=encrypted_uuid_of_trader_3
    TRADER_4_UUID=encrypted_uuid_of_trader_4
    TRADER_5_UUID=encrypted_uuid_of_trader_5
    TRADER_6_UUID=encrypted_uuid_of_trader_6
    TRADER_7_UUID=encrypted_uuid_of_trader_7
    TRADER_8_UUID=encrypted_uuid_of_trader_8
    TRADER_9_UUID=encrypted_uuid_of_trader_9
    ```
4. Start the program:
    ```
    python bot.py
    #then start all the tradercopy.py with 15 seconds delay between each one (not optimized i know)
    ```
5. Telegram Bot Setup: Open your Telegram bot and follow the on-screen prompts to set up your Bybit API key, desired leverage, and other configurations.

### Security

Ensure your `.env` file remains private. Never share or expose your API keys. Use environment variables or secret management tools to securely handle them.

### Contributing

Contributions are what make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.
