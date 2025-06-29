import pandas as pd

def strategy_vwap_bounce(df):
    if len(df) < 3:
        return 0, ["לא מספיק נרות"]

    last = df.iloc[-1]
    prev = df.iloc[-2]

    buy_score = 0
    reasons = []

    # חישוב VWAP
    df["vwap"] = (df["high"] + df["low"] + df["close"]) / 3
    df["cum_vol"] = df["volume"].cumsum()
    df["cum_vol_price"] = (df["vwap"] * df["volume"]).cumsum()
    df["vwap_line"] = df["cum_vol_price"] / df["cum_vol"]

    vwap = df["vwap_line"].iloc[-1]

    # תנאי 1: המחיר ירד מתחת ל-VWAP ואז חזר מעליו
    if prev["close"] < vwap and last["close"] > vwap:
        buy_score += 1
        reasons.append("קפיצה מעל VWAP לאחר ירידה")

    # תנאי 2 (רשות): נפח מסחר גבוה
    avg_volume = df["volume"].rolling(window=20).mean().iloc[-1]
    if last["volume"] > avg_volume:
        buy_score += 1
        reasons.append("נפח מסחר גבוה מהממוצע")

    return buy_score, reasons
