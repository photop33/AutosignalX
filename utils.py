import requests
from datetime import datetime
import pandas as pd
import time
import os
from my_keys import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from config import INTERVAL,VOLUME_LOOKBACK,EMA_LONG
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
from config import RSI_OVERSOLD, EMA_SHORT, EMA_LONG, VOLUME_LOOKBACK, VOLATILITY_THRESHOLD, MIN_VOLUME, INTERVAL, RISK_REWARD_RATIO, EXPECTED_PROFIT_MIN


def log_rejection(symbol, reason, strategy_name="unknown"):
    print(f"🚫 {symbol} נפסל - {reason} ({strategy_name})")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/rejected_signals_log.csv", "a", encoding="utf-8") as f:
        f.write(f"{now},{symbol},{reason},{strategy_name}\n")


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})


def get_klines(client, symbol, interval, limit=100):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df.astype(float, errors='ignore')
    return df


def get_next_id():
    counter_file = "logs/id_counter.txt"
    if not os.path.exists(counter_file):
        with open(counter_file, "w") as f:
            f.write("0")
    with open(counter_file, "r") as f:
        last_id = int(f.read().strip())
    next_id = last_id + 1
    with open(counter_file, "w") as f:
        f.write(str(next_id))
    return next_id

def log_signal(symbol, price_now, strategy_name, tp, sl, client):
    from config import RSI_OVERSOLD, EMA_SHORT, EMA_LONG, VOLUME_LOOKBACK, VOLATILITY_THRESHOLD, MIN_VOLUME, INTERVAL, RISK_REWARD_RATIO, EXPECTED_PROFIT_MIN

    now_dt = datetime.now()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_str = now_dt.strftime('%Y%m%d_%H%M%S')
    counter_id = get_next_id()
    signal_id = f"{symbol}_{timestamp_str}-{counter_id}"

    # 🟡 קבלת volume מהקנדל האחרון
    try:
        klines = get_klines(client, symbol, INTERVAL, limit=1)
        volume = klines["volume"].iloc[-1]
    except Exception as e:
        volume = -1  # כדי שתדע שנכשל
        log_rejection(symbol, f"Volume fetch failed: {e}", strategy_name)

    # ✍️ config snapshot
    snapshot = {
        "RSI_OVERSOLD": RSI_OVERSOLD,
        "EMA_SHORT": EMA_SHORT,
        "EMA_LONG": EMA_LONG,
        "VOLUME_LOOKBACK": VOLUME_LOOKBACK,
        "VOLATILITY_THRESHOLD": VOLATILITY_THRESHOLD,
        "MIN_VOLUME": MIN_VOLUME,
        "INTERVAL": INTERVAL,
        "RISK_REWARD_RATIO": RISK_REWARD_RATIO,
        "EXPECTED_PROFIT_MIN": EXPECTED_PROFIT_MIN,
        "VOLUME": volume
    }

    snapshot_file = "logs/signals_log.csv"
    snapshot_header = "signal_time,symbol,entry_price,TP,SL,strategy,signal_id," + ",".join(snapshot.keys()) + "\n"
    snapshot_line = f"{now_str},{symbol},{price_now},{tp},{sl},{strategy_name},{signal_id}," + ",".join(str(v) for v in snapshot.values()) + "\n"

    if not os.path.exists(snapshot_file):
        with open(snapshot_file, "w", encoding="utf-8") as f:
            f.write(snapshot_header)

    with open(snapshot_file, "a", encoding="utf-8") as f:
        f.write(snapshot_line)
