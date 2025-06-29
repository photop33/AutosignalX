import ta

def calculate_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close']).rsi()
    df['macd'] = ta.trend.MACD(close=df['close']).macd()
    df['adx'] = ta.trend.ADXIndicator(high=df['high'], low=df['low'], close=df['close']).adx()
    df['ema_short'] = ta.trend.EMAIndicator(close=df['close'], window=12).ema_indicator()
    df['ema_long'] = ta.trend.EMAIndicator(close=df['close'], window=26).ema_indicator()
    bb = ta.volatility.BollingerBands(close=df['close'])
    df['bb_width'] = bb.bollinger_hband() - bb.bollinger_lband()
    return df
