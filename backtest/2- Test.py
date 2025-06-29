import pandas as pd
from binance.client import Client
from datetime import datetime, timezone
import ta
import os
from concurrent.futures import ThreadPoolExecutor
from my_keys import BINANCE_API_KEY, BINANCE_API_SECRET
import pytz
import re

israel_tz = pytz.timezone("Asia/Jerusalem")
client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)

# --- נתיבים
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
signals_path = os.path.join(log_dir, "signals_log.csv")

# --- פונקציה שמנקה את עמודת הזמן
def clean_signal_times(df):
    def clean_time_string(t):
        if pd.isna(t):
            return None
        t = str(t).strip()
        # הסרת תווים לא רלוונטיים
        t = re.sub(r"[^\d:/\s\-]", "", t)
        # ניסיון להמיר לפורמט תקין
        for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%Y/%m/%d %H:%M"):
            try:
                return datetime.strptime(t, fmt)
            except:
                continue
        return pd.NaT  # אם נכשל, החזר ערך לא תקני

    df["time"] = df["time"].apply(clean_time_string)
    df = df.dropna(subset=["time"])  # הסרת שורות עם תאריך לא תקין
    df["time"] = pd.to_datetime(df["time"]).dt.tz_localize("Asia/Jerusalem")
    return df

# --- טען את קובץ הסיגנלים
signals_df = pd.read_csv(signals_path, header=None, names=["time", "symbol", "entry_price", "TP", "SL", "strategy"])
signals_df = clean_signal_times(signals_df)

# Cache למחירי נוכחיים
price_cache = {}



def get_price(symbol):
    if symbol not in price_cache:
        try:
            price_cache[symbol] = float(client.get_symbol_ticker(symbol=symbol)["price"])
        except:
            price_cache[symbol] = None
    return price_cache[symbol]

# ניתוח סיגנל בודד
def analyze_signal(row):
    try:
        symbol = row["symbol"]
        entry_price = float(row["entry_price"])
        take_profit = float(row["TP"])
        stop_loss = float(row["SL"])
        signal_time = row["time"]
        strategy = row["strategy"]

        # נרות היסטוריים לאינדיקטורים
        start_time = signal_time - pd.Timedelta(minutes=250)
        klines = client.get_klines(
            symbol=symbol,
            interval="1m",
            startTime=int(start_time.timestamp() * 1000),
            limit=50
        )
        df_klines = pd.DataFrame(klines, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        df_klines[['high', 'low', 'close']] = df_klines[['high', 'low', 'close']].astype(float)

        # אינדיקטורים
        df_klines['rsi'] = ta.momentum.RSIIndicator(close=df_klines['close']).rsi()
        df_klines['macd'] = ta.trend.MACD(close=df_klines['close']).macd()
        df_klines['adx'] = ta.trend.ADXIndicator(high=df_klines['high'], low=df_klines['low'], close=df_klines['close']).adx()
        # הוסף חישוב EMA קצר וארוך (למשל 12 ו־26)
        df_klines['ema_short'] = ta.trend.EMAIndicator(close=df_klines['close'], window=12).ema_indicator()
        df_klines['ema_long'] = ta.trend.EMAIndicator(close=df_klines['close'], window=26).ema_indicator()

        last = df_klines.iloc[-1]
        rsi = round(last['rsi'], 2)
        macd = round(last['macd'], 4)
        adx = round(last['adx'], 2)
        volume_avg = df_klines['volume'].astype(float).rolling(window=20).mean().iloc[-1]
        volatility = (df_klines['high'] - df_klines['low']).rolling(window=20).mean().iloc[-1]
        trend_strength = abs(last['ema_short'] - last['ema_long'])
        bb = ta.volatility.BollingerBands(close=df_klines['close'])
        bb_width = (bb.bollinger_hband() - bb.bollinger_lband()).iloc[-1]

        symbol_category_map = {
            "BTCUSDT": "BTC",
            "ETHUSDT": "ALT",
            "SOLUSDT": "ALT",
            "TSLA": "STOCK",
            "AAPL": "STOCK"
        }
        symbol_category = symbol_category_map.get(symbol, "OTHER")

        # נרות עתידיים לניתוח TP/SL
        future_klines = client.get_klines(symbol=symbol, interval="1m",
                                          startTime=int(signal_time.timestamp() * 1000),
                                          limit=288)
        result = "⏳ Still Open"
        hit_time = None
        tp_time = None
        sl_time = None

        # נרות עתידיים עד פגיעה ב-TP או SL (ללא מגבלת זמן)
        result = "⏳ Still Open"
        hit_time = None
        tp_time = None
        sl_time = None

        future_klines = []
        start_ts = int(signal_time.timestamp() * 1000)
        max_minutes = 1440  # עד 24 שעות קדימה
        collected = 0
        limit_per_batch = 1000

        while collected < max_minutes:
            klines = client.get_klines(
                symbol=symbol,
                interval="1m",
                startTime=start_ts,
                limit=min(limit_per_batch, max_minutes - collected)
            )
            if not klines:
                break

            future_klines.extend(klines)
            last_time = klines[-1][0]
            start_ts = last_time + 60_000  # דקה קדימה
            collected += len(klines)

            for k in klines:
                open_time = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).astimezone(israel_tz)
                high = float(k[2])
                low = float(k[3])
                if tp_time is None and high >= take_profit:
                    tp_time = open_time
                if sl_time is None and low <= stop_loss:
                    sl_time = open_time
                if tp_time or sl_time:
                    break

            if tp_time or sl_time:
                break

        # המשך אותו דבר כרגיל
        if tp_time and sl_time:
            if tp_time <= sl_time:
                result = "✅ TP Hit"
                hit_time = tp_time
            else:
                result = "❌ SL Hit"
                hit_time = sl_time
        elif tp_time:
            result = "✅ TP Hit"
            hit_time = tp_time
        elif sl_time:
            result = "❌ SL Hit"
            hit_time = sl_time
        else:
            result = "⏳ Still Open"
            hit_time = None

        # מחיר נוכחי
        current_price = get_price(symbol)
        if current_price is None:
            return None

        # חישוב רווח/הפסד
        if result == "✅ TP Hit":
            pnl = ((take_profit - entry_price) / entry_price) * 100
        elif result == "❌ SL Hit":
            pnl = ((stop_loss - entry_price) / entry_price) * 100
        else:
            pnl = ((current_price - entry_price) / entry_price) * 100

        time_to_hit = (hit_time - signal_time).total_seconds() / 3600 if hit_time else "N/A"

        return {
            "symbol": symbol,
            "signal_time": signal_time,
            "signal": "BUY",
            "entry_price": entry_price,
            "TL": take_profit,
            "SL": stop_loss,
            "price_now": round(current_price, 4),
            "תוצאה": result,
            "PnL_%": round(pnl, 2),
            "cross_line_time": hit_time.astimezone(israel_tz).strftime("%Y-%m-%d %H:%M:%S") if hit_time else "N/A",
            "Target spend": round(time_to_hit, 2) if time_to_hit != "N/A" else "N/A",
            "strategy": strategy,
            "RSI": rsi,
            "MACD": macd,
            "ADX": adx,
            "ema_short": round(last['ema_short'], 4),
            "ema_long": round(last['ema_long'], 4),
            "Volume_avg": round(volume_avg, 2),
            "Volatility": round(volatility, 4),
            "Trend_strength": round(trend_strength, 4),
            "BB_width": round(bb_width, 4),
            "Symbol_category": symbol_category

        }


    except Exception as e:
        print(f"שגיאה ב-{row['symbol']}: {e}")
        return None

# הרצה מקבילית
with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(analyze_signal, [row for _, row in signals_df.iterrows()]))

# שמירה

results = [r for r in results if r]
results_df = pd.DataFrame(results)
results_df["cross_line_time"] = pd.to_datetime(results_df["cross_line_time"], errors="coerce").dt.tz_localize(None)
results_df["signal_time"] = pd.to_datetime(results_df["signal_time"], errors="coerce").dt.tz_localize(None)

output_path = os.path.join(log_dir, "signal_backtest_results_with_indicators.xlsx")
results_df.to_excel(output_path, index=False)

print(f"✅ נשמר הקובץ: {output_path} | נוספו {len(results)} שורות.")
