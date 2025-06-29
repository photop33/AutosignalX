import pandas as pd
from ta.trend import MACD
from config import *

def compute_supertrend(df, period=10, multiplier=3.0):
    hl2 = (df['high'] + df['low']) / 2
    atr = df['high'].rolling(period).max() - df['low'].rolling(period).min()
    atr = atr.rolling(period).mean()
    supertrend = hl2 - multiplier * atr

    direction = pd.Series(True, index=df.index)  # True = uptrend
    for i in range(1, len(df)):
        if df['close'].iloc[i] > supertrend.iloc[i - 1]:
            direction.iloc[i] = True
        elif df['close'].iloc[i] < supertrend.iloc[i - 1]:
            direction.iloc[i] = False
        else:
            direction.iloc[i] = direction.iloc[i - 1]
            if direction.iloc[i] and supertrend.iloc[i] < supertrend.iloc[i - 1]:
                supertrend.iloc[i] = supertrend.iloc[i - 1]
            elif not direction.iloc[i] and supertrend.iloc[i] > supertrend.iloc[i - 1]:
                supertrend.iloc[i] = supertrend.iloc[i - 1]

    df['supertrend'] = supertrend
    df['supertrend_dir'] = direction
    return df


def strategy_supertrend_macd(df):
    if len(df) < 50:
        return 0, ["לא מספיק נרות למסחר"]

    # חישוב MACD
    macd_indicator = MACD(close=df["close"])
    df["macd"] = macd_indicator.macd()
    df["macd_signal"] = macd_indicator.macd_signal()

    # חישוב SuperTrend
    df = compute_supertrend(df)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    buy_score = 0
    reasons = []

    # תנאי 1: MACD חוצה מעלה את ה-signal
    if prev['macd'] < prev['macd_signal'] and last['macd'] > last['macd_signal']:
        buy_score += 1
        reasons.append("MACD חצה מעלה")

    # תנאי 2: SuperTrend מעיד על מגמת עלייה
    if last['supertrend_dir']:
        buy_score += 1
        reasons.append("SuperTrend מראה מגמת עלייה")

    return buy_score, reasons
