
import pandas as pd
import ta

def strategy_bollinger_macd(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    buy_score = 0
    reasons = []

    # ✅ תנאי 1: Bollinger Band Squeeze
    df['bb_width'] = df['bb_upper'] - df['bb_lower']
    bb_avg = df['bb_width'].rolling(20).mean()
    if df['bb_width'].iloc[-1] < bb_avg.iloc[-1] * 0.8:
        buy_score += 1
        reasons.append("בולינגר צר (Squeeze)")

    # ✅ תנאי 2: MACD חצה מעלה
    if prev['macd'] < prev['macd_signal'] and last['macd'] > last['macd_signal']:
        buy_score += 1
        reasons.append("MACD חצה מעלה")

    return buy_score, reasons
