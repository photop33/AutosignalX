import ta

def compute_indicators(df):
    min_window = 10     # מתחת לזה – לא מחשבים בכלל
    max_window = 14    # גודל ברירת מחדל

    available_window = min(len(df), max_window)

    if len(df) < min_window:
        print(f"⚠️ פחות מ-{min_window} נרות – מדלג על חישוב אינדיקטורים")
        return df

    # RSI
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=available_window).rsi()

    # MACD (אפשר להשאיר ברירת מחדל)
    macd = ta.trend.MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()

    # EMA
    df['ema_short'] = ta.trend.EMAIndicator(close=df['close'], window=9).ema_indicator()
    df['ema_long'] = ta.trend.EMAIndicator(close=df['close'], window=21).ema_indicator()

    # Bollinger Bands (רק אם יש מספיק ל-20 נרות)
    if len(df) >= 20:
        bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['bb_mid'] = bb.bollinger_mavg()
    else:
        df['bb_upper'] = df['bb_lower'] = df['bb_mid'] = None

    # ATR עם חלון דינמי
    df['atr'] = ta.volatility.AverageTrueRange(
        high=df['high'], low=df['low'], close=df['close'], window=available_window
    ).average_true_range()

    return df
