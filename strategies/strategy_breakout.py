LOOKBACK_PERIOD = 20  # כמות נרות אחורה לבדיקה
VOLUME_CONFIRMATION = True


def strategy_breakout(df):
    if len(df) < LOOKBACK_PERIOD + 2:
        return 0, ["לא מספיק נרות לבדיקת פריצה"]

    last = df.iloc[-1]
    prev = df.iloc[-2]

    highest_high = df['high'].iloc[-LOOKBACK_PERIOD - 1:-1].max()
    lowest_low = df['low'].iloc[-LOOKBACK_PERIOD - 1:-1].min()
    avg_volume = df['volume'].iloc[-LOOKBACK_PERIOD - 1:-1].mean()

    reasons = []
    score = 0

    if prev['close'] <= highest_high and last['close'] > highest_high:
        score += 1
        reasons.append("פריצה כלפי מעלה")

    if VOLUME_CONFIRMATION and last['volume'] > avg_volume:
        score += 1
        reasons.append("ווליום תומך בפריצה")

    return score, reasons
