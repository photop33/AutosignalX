from config import RSI_OVERSOLD, EMA_SHORT, EMA_LONG, VOLUME_LOOKBACK
def strategy_rsi_macd(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    buy_score = 0
    reasons = []

    if prev['rsi'] < 30 and last['rsi'] > 30:
        buy_score += 1
        reasons.append("RSI יצא ממכירת יתר")

    if prev['macd'] < prev['macd_signal'] and last['macd'] > last['macd_signal']:
        buy_score += 1
        reasons.append("MACD חצה מעלה")

    if prev['ema_short'] < prev['ema_long'] and last['ema_short'] > last['ema_long']:
        buy_score += 1
        reasons.append("EMA חצה")

    avg_vol = df['volume'].rolling(20).mean().iloc[-1]
    if last['volume'] > avg_vol:
        buy_score += 1
        reasons.append("ווליום גבוה מהממוצע")

    return buy_score
