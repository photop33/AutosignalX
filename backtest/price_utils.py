from binance.client import Client
from my_keys import BINANCE_API_KEY, BINANCE_API_SECRET

client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)
_price_cache = {}

def get_price(symbol):
    if symbol not in _price_cache:
        try:
            _price_cache[symbol] = float(client.get_symbol_ticker(symbol=symbol)["price"])
        except:
            _price_cache[symbol] = None
    return _price_cache[symbol]
