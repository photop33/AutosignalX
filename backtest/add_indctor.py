import pandas as pd
from binance.client import Client
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import ta

# Binance API
from my_keys import BINANCE_API_KEY, BINANCE_API_SECRET
client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)


def enrich_signals_with_indicators(file_path: str, output_path: str):
    israel_tz = pytz.timezone("Asia/Jerusalem")
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    df = pd.read_excel(file_path)
    if 'symbol' not in df.columns or 'signal_time' not in df.columns:
        raise Exception("חסרות עמודות 'symbol' או 'signal_time' בקובץ")

    df["signal_time"] = pd.to_datetime(df["signal_time"], errors="coerce")

    all_klines = defaultdict(pd.DataFrame)
    indicators = {
        "binance_volume": [],
        "macd": [], "macd_signal": [],
        "adx": [], "ema_short": [], "ema_long": [],
        "bb_width": [], "volatility": [],
        "rsi": []
    }

    # Determine how many days of data are needed per symbol
    symbol_days_map = {}
    for symbol in df["symbol"].unique():
        symbol_times = df[df["symbol"] == symbol]["signal_time"].dropna()
        if not symbol_times.empty:
            earliest = israel_tz.localize(symbol_times.min()).astimezone(pytz.utc)
            days_needed = max(1, (now_utc - earliest).days + 1)
            symbol_days_map[symbol] = days_needed

    # Fetch klines and calculate indicators
    for symbol, days_needed in symbol_days_map.items():
        try:
            print(f"⏳ טוען {days_needed} ימים עבור {symbol}...")
            start_str = f"{days_needed} days ago UTC"
            klines = client.get_historical_klines(symbol, interval="1m", start_str=start_str)
            kdf = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            kdf["timestamp"] = pd.to_datetime(kdf["timestamp"], unit="ms").dt.tz_localize("UTC")
            kdf.set_index(kdf["timestamp"], inplace=True)
            kdf = kdf.astype(float, errors='ignore')

            # Calculate indicators
            kdf["macd"] = ta.trend.macd(kdf["close"])
            kdf["macd_signal"] = ta.trend.macd_signal(kdf["close"])
            kdf["adx"] = ta.trend.adx(kdf["high"], kdf["low"], kdf["close"])
            kdf["ema_short"] = ta.trend.ema_indicator(kdf["close"], window=9)
            kdf["ema_long"] = ta.trend.ema_indicator(kdf["close"], window=21)
            bb = ta.volatility.BollingerBands(kdf["close"])
            kdf["bb_width"] = bb.bollinger_wband()
            kdf["volatility"] = kdf["close"].rolling(window=10).std()
            kdf["rsi"] = ta.momentum.RSIIndicator(kdf["close"], window=14).rsi()

            all_klines[symbol] = kdf
            print(f"✅ {symbol} נרות נטענו: {len(kdf)}")
        except Exception as e:
            print(f"❌ שגיאה בטעינת {symbol}: {e}")
            all_klines[symbol] = pd.DataFrame()

    # Extract indicators per row
    for i, row in df.iterrows():
        symbol = row["symbol"]
        signal_time = row["signal_time"]
        try:
            utc_time = israel_tz.localize(signal_time).astimezone(pytz.utc)
            kdf = all_klines[symbol]

            if kdf.empty:
                for key in indicators:
                    indicators[key].append(None)
                continue

            idx = kdf.index.get_indexer([utc_time], method="nearest")[0]
            row_data = kdf.iloc[idx]

            indicators["binance_volume"].append(row_data["volume"])
            indicators["macd"].append(row_data["macd"])
            indicators["macd_signal"].append(row_data["macd_signal"])
            indicators["adx"].append(row_data["adx"])
            indicators["ema_short"].append(row_data["ema_short"])
            indicators["ema_long"].append(row_data["ema_long"])
            indicators["bb_width"].append(row_data["bb_width"])
            indicators["volatility"].append(row_data["volatility"])
            indicators["rsi"].append(row_data["rsi"])

            print(f"📊 {symbol} | {signal_time} → Volume: {row_data['volume']:.2f}, MACD: {row_data['macd']:.4f}, RSI: {row_data['rsi']:.2f}")
        except Exception as e:
            print(f"⚠️ שגיאה בשורה {i} ({symbol}): {e}")
            for key in indicators:
                indicators[key].append(None)

    # Add columns to DataFrame
    for col, values in indicators.items():
        df[col] = values

    # Save to file
    df.to_excel(output_path, index=False)
    print(f"\n✅ הקובץ נשמר עם כל האינדיקטורים: {output_path}")


