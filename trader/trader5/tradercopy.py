import os
import requests
import json
import time
import logging
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

load_dotenv()


log_filename = os.path.join(os.path.dirname(__file__), 'trade.log')
trade_info_fichier = os.path.join(os.path.dirname(__file__), 'trader5.json') 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.getLogger('').addHandler(file_handler)




def trade(symbol, direction):
    # Load trade info from json file
    with open(trade_info_fichier) as f:
        trade_info = json.load(f)

    # Set up logging
    logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    if trade_info == []:
        logging.info("No data to trade")
    else:
        # Loop through each trade in trade_info
        for trade in trade_info:
            try:
                # Create an authenticated session with Bybit's Unified Trading API
                session = HTTP(api_key=trade['bybit_api_key'], api_secret=trade['bybit_api_secret'])
            except Exception as e:
                logging.error(f"Error creating authenticated session for {symbol} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Error: {e}")
            try:
                # Set the leverage for the specified symbol and direction
                response = session.switch_margin_mode(
                    category="linear",
                    symbol=symbol,
                    tradeMode=int(trade['leviertype']),
                    buyLeverage=trade['leverage'],
                    sellLeverage=trade['leverage'],
                        )

                if response['retMsg'] == 'OK':
                    logging.info(f"margin mode set successfully for {symbol} {direction} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Leverage: {trade['leverage']}")
                else:
                    logging.error(f"Error setting margin mode for {symbol} {direction} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Leverage: {trade['leverage']}. Response: {response}")
            except Exception as e:
                logging.error(f"Error setting margin mode for {symbol} {direction} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Leverage: {trade['leverage']}. Error: {e}")
                logging.info("Continuing to place order...")

            try:
                # Set the leverage for the specified symbol and direction
                response = session.set_leverage(
                    category="linear",
                    symbol=symbol,
                    buyLeverage=trade['leverage'],
                    sellLeverage=trade['leverage'],
                )

                if response['retMsg'] == 'OK':
                    logging.info(f"Leverage set successfully for {symbol} {direction} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Leverage: {trade['leverage']}")
                else:
                    logging.error(f"Error setting leverage for {symbol} {direction} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Leverage: {trade['leverage']}. Response: {response}")
            except Exception as e:
                logging.error(f"Error setting leverage for {symbol} {direction} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Leverage: {trade['leverage']}. Error: {e}")
                logging.info("Continuing to place order...")

        # Get the current price of the symbol
            try:
                response = session.get_tickers(
                    category="linear",
                    symbol=symbol,
                )

                if response and 'result' in response and 'list' in response['result'] and len(response['result']['list']) > 0:
                    price = float(response['result']['list'][0].get('lastPrice', None))
                    if price is not None:
                        # Calculate order size as usdt_size / price
                        usdt_size = float(trade['usdt_amount']) 
                        size = usdt_size * int(trade['leverage'])
                        size = round(usdt_size / price, 3)
                        size = round(size * int(trade['leverage']), 3)
                        logging.info(f"Placing a market order to buy {size} contracts of {symbol} at {price} USDT per contract for {direction} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Leverage: {trade['leverage']}.")
                        # Place a market order to buy the specified size of contracts
                        try:
                            response = session.place_order(
                                category="linear",
                                symbol=symbol,
                                side=direction,
                                orderType="Market",
                                qty=size,
                                leverage=int(trade['leverage']),
                            )

                            if 'result' in response and response['result']:
                                logging.info(f"Trade placed successfully for {symbol} {direction} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Leverage: {trade['leverage']}. Response: {response}")
                            else:
                                logging.error(f"Error placing trade for {symbol} {direction} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Leverage: {trade['leverage']}. Response: {response}")

                        except Exception as e:
                            logging.error(f"Error placing trade for {symbol} {direction} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Leverage: {trade['leverage']}. Error: {e}")
                            logging.info("Continuing to next trade...")

                    else:
                        logging.error(f"Error getting ticker data for {symbol}. Last price not found. Response: {response}")

                else:
                    logging.error(f"Error getting ticker data for {symbol}. Response: {response}")

            except Exception as e:
                logging.error(f"Error getting ticker data for {symbol}. Error: {e}")
                logging.info("Continuing to next trade...")



def close_trade_on_symbol(symbol):
    # Load trade info from json file
    with open(trade_info_fichier) as f:
        trade_info = json.load(f)

    # Set up logging
    logging.basicConfig(filename='trade.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    if trade_info == []:
        logging.info("No data to close trade")
    else :
        # Loop through each trade in trade_info
        for trade in trade_info:
            try:
                # Create an authenticated session with Bybit's Unified Trading API
                session = HTTP(api_key=trade['bybit_api_key'], api_secret=trade['bybit_api_secret'])

                # Get the current positions for the symbol
                response = session.get_positions(
                    category="linear",
                    symbol=symbol,
                )

                if response and 'result' in response and 'list' in response['result'] and len(response['result']['list']) > 0:
                    for position in response['result']['list']:
                        # Get the size and side of the position
                        size = float(position['size'])
                        side = position['side']

                        # Determine the opposite direction of the position
                        opposite_direction = "Sell" if side == "Buy" else "Buy"

                        # Place a market order in the opposite direction to close the trade
                        response = session.place_order(
                            category="linear",
                            symbol=symbol,
                            side=opposite_direction,
                            orderType="Market",
                            qty=size,
                        )

                        if 'result' in response and response['result']:
                            logging.info(f"Trade closed successfully for {symbol} {side} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Response: {response}")
                        else:
                            logging.error(f"Error closing trade for {symbol} {side} trade. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Response: {response}")

                else:
                    logging.error(f"Error getting position data for {symbol}. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Response: {response}")

            except Exception as e:
                logging.error(f"An error occurred while processing trade for {symbol}. API keys: {trade['bybit_api_key']}, {trade['bybit_api_secret']}. Error: {e}")


headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
}

json_data = {
    'encryptedUid': os.getenv('TRADER_5_UUID'),
    'tradeType': 'PERPETUAL',
}

filename = os.path.join(os.path.dirname(__file__), 'symbols.json')

previous_symbols = {}

if os.path.exists(filename):
    with open(filename, 'r') as f:
        try:
            previous_symbols = json.load(f)
        except json.JSONDecodeError:
            pass

counter = 0 # initialize counter
no_change_threshold = 30

while True:
    try:
        response = requests.post('https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition', headers=headers, json=json_data)
        response.raise_for_status()
        data = response.json()




        current_symbols = {}

        for item in data['data']['otherPositionRetList']:
            amount = item['amount']
            symbol = item['symbol']
            current_symbols[symbol] = amount

        new_symbols = set(current_symbols.keys()) - set(previous_symbols.keys())
        removed_symbols = set(previous_symbols.keys()) - set(current_symbols.keys())

        symbols_added = []
        symbols_removed = []
        symbols_with_increased_amount = []

        if new_symbols:
            symbols_added = list(new_symbols)
            logging.info(f"New symbols found: {symbols_added}")
            for symbol in symbols_added:
                if current_symbols[symbol] > 0:
                    trade(symbol, "Buy")
                elif current_symbols[symbol] < 0:
                    trade(symbol, "Sell")
        if removed_symbols:
            symbols_removed = list(removed_symbols)
            logging.info(f"Removed symbols: {symbols_removed}")
            for symbol in removed_symbols:
                close_trade_on_symbol(symbol)
            

        for symbol in current_symbols:
            if symbol in previous_symbols and abs(current_symbols[symbol]) > abs(previous_symbols[symbol]):
                increase_percentage = abs(current_symbols[symbol] - previous_symbols[symbol]) / abs(previous_symbols[symbol])
                if increase_percentage >= 1.5:
                    symbols_with_increased_amount.append(symbol)
                    logging.info(f"Symbol {symbol} amount increased: {previous_symbols[symbol]} -> {current_symbols[symbol]}")
                    if current_symbols[symbol] > previous_symbols[symbol]:
                        direction = "Buy"
                    else:
                        direction = "Sell"
                    trade(symbol, direction)


        if not symbols_added and not symbols_removed and not symbols_with_increased_amount:
            counter += 1 # increment counter
            if counter == no_change_threshold:
                logging.info("No changes")
                counter = 0 # reset counter

        previous_symbols = current_symbols

        with open(filename, 'w') as f:
            json.dump(previous_symbols, f)

    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        logging.error(f"An error occurred while making the request: {e}")

    time.sleep(90) # Wait for 90 seconds before making the next request

