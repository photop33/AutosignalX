def is_bullish_candle(df):
    return df['close'].iloc[-1] > df['close'].iloc[-2]

def is_macd_cross_up(df):
    return df['macd'].iloc[-2] < df['macd_signal'].iloc[-2] and df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]

def is_volume_strong(df):
    df['volume'] = df['close'] * df['high']
    return df['volume'].iloc[-1] >= df['volume'].median()

def rsi_buy_pattern(rsi_series):
    return rsi_series.iloc[0] >= 30 and rsi_series.iloc[1] <= 32 and rsi_series.iloc[2] <= 32
