import pandas as pd
from datetime import datetime, timezone
import os
from binance.client import Client
from indicators_utils import calculate_indicators
from price_utils import get_price
import pytz

israel_tz = pytz.timezone("Asia/Jerusalem")
client = Client()  # Already authenticated via price_utils

def analyze_signal(row):
    try:
        symbol = row["symbol"]
        entry_price = float(row["entry_price"]) if "entry_price" in row else float(row["price"])
        tp = float(row["TP"])
        sl = float(row["SL"])
        strategy = row["strategy"]
        signal_time = row["time"]
        signal_id = row.get("signal_id", "N/A")  # הוספה כאן

        # הורדת נרות עבר
        start_time = signal_time - pd.Timedelta(minutes=250)
        klines = client.get_klines(symbol=symbol, interval="1m", startTime=int(start_time.timestamp() * 1000),
                                   limit=200)
        df_klines = pd.DataFrame(klines, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        df_klines[['high', 'low', 'close']] = df_klines[['high', 'low', 'close']].astype(float)
        df_klines = calculate_indicators(df_klines)
        last = df_klines.iloc[-1]

        # הורדת נרות עתידיים לניתוח TP/SL
        future_klines = []
        start_ts = int(signal_time.timestamp() * 1000)
        max_minutes = 1440
        collected = 0

        tp_time, sl_time = None, None
        while collected < max_minutes:
            klines = client.get_klines(symbol=symbol, interval="1h", startTime=start_ts, limit=min(1000, max_minutes - collected))
            if not klines: break
            future_klines.extend(klines)
            for k in klines:
                ts = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).astimezone(israel_tz)
                high = float(k[2])
                low = float(k[3])
                if not tp_time and high >= tp: tp_time = ts
                if not sl_time and low <= sl: sl_time = ts
                if tp_time or sl_time: break
            if tp_time or sl_time: break
            start_ts = klines[-1][0] + 60000
            collected += len(klines)

        result = "⏳ Still Open"
        hit_time = None
        if tp_time and sl_time:
            if tp_time <= sl_time:
                result, hit_time = "✅ TP Hit", tp_time
            else:
                result, hit_time = "❌ SL Hit", sl_time
        elif tp_time:
            result, hit_time = "✅ TP Hit", tp_time
        elif sl_time:
            result, hit_time = "❌ SL Hit", sl_time

        current_price = get_price(symbol)
        if current_price is None: return None

        if result == "✅ TP Hit":
            pnl = ((tp - entry_price) / entry_price) * 100
        elif result == "❌ SL Hit":
            pnl = ((sl - entry_price) / entry_price) * 100
        else:
            pnl = ((current_price - entry_price) / entry_price) * 100

        return {
            "signal_id": signal_id,  # ✅ תוספת קריטית
            "symbol": symbol,
            "signal_time": signal_time,
            "entry_price": entry_price,
            "TL": tp,
            "SL": sl,
            "price_now": round(current_price, 4),
            "תוצאה": result,
            "PnL_%": round(pnl, 2),
            "cross_line_time": hit_time.strftime("%Y-%m-%d %H:%M:%S") if hit_time else "N/A",
            "strategy": strategy,
            # "RSI": round(last["rsi"], 2) if not pd.isna(last["rsi"]) else None,
            # "MACD": round(last["macd"], 4),
            # "ADX": round(last["adx"], 2),
            # "ema_short": round(last["ema_short"], 4),
            # "ema_long": round(last["ema_long"], 4),
            # "BB_width": round(last["bb_width"], 4),
            # "volume" : round(float(last.get("volume", 0)), 2),
        }

    except Exception as e:
        print(f"שגיאה ב-{row['symbol']}: {e}")
        return None
