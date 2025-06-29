

def strategy_breakout_volume(df):
    last = df.iloc[-1]
    high_last_20 = df['high'].iloc[-21:-1].max()
    avg_volume = df['volume'].rolling(20).mean().iloc[-1]

    buy_score = 0
    reasons = []

    # ✅ תנאי 1: פריצה מעל התנגדות
    if last['close'] > high_last_20:
        buy_score += 1
        reasons.append("פריצה מעל התנגדות אחרונה")

    # ✅ תנאי 2: ווליום גבוה מהממוצע
    if last['volume'] > avg_volume * 1.5:
        buy_score += 1
        reasons.append("ווליום גבוה מהממוצע")

    return buy_score, reasons
