from my_keys import BINANCE_API_KEY, BINANCE_API_SECRET, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

ACTIVE_STRATEGIES = [
    "strategy_rsi_macd",
    "strategy_bollinger_macd",
    "strategy_breakout_volume",
    "strategy_breakout",
    "strategy_candlestick",
    "strategy_supertrend_macd",
    "strategy_vwap_bounce"
]

STRATEGY_THRESHOLDS = {
    "strategy_rsi_macd": 3,
    "strategy_bollinger_macd": 2,
    "strategy_breakout_volume": 2,
    "strategy_breakout":2,
    "strategy_candlestick":1,
    "strategy_supertrend_macd":2,
    "strategy_vwap_bounce":2
}





# ==== תנאים לאינדיקטורים ====
RSI_OVERSOLD = 30               # רמת RSI שממנה נחשב "מכירת יתר"
EMA_SHORT = 9                   # ממוצע נע קצר
EMA_LONG = 21                   # ממוצע נע ארוך
VOLUME_LOOKBACK = 20           # מספר נרות לחישוב ממוצע ווליום

# ==== תנאי BUY כללי ====

# ==== תנודתיות וסינון ====
VOLATILITY_THRESHOLD = 0.00    # סף שינוי יומי מינימלי לזיהוי נכסים תנודתיים
MIN_VOLUME = 50000             # נפח מסחר מינימלי ב-24 שעות
INTERVAL = '15m'               # טווח נר ברירת מחדל

# ==== TP/SL ====
RISK_REWARD_RATIO = 2          # יחס סיכון/רווח (לפי ATR)
EXPECTED_PROFIT_MIN = 0.00    # רווח מינימלי בעסקה כדי להיכנס