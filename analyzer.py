from utils import get_klines, log_rejection, send_telegram, log_signal
from indicators import compute_indicators
from config import *
import ta
from config import EMA_LONG, VOLUME_LOOKBACK, RISK_REWARD_RATIO, EXPECTED_PROFIT_MIN
from datetime import datetime, timedelta

def price_changed_significantly(symbol, new_price, old_price, threshold=0.003):
    return abs(new_price - old_price) / old_price > threshold

LAST_SIGNALS = {}  # מפת מפתחות (symbol, strategy) לזמן שליחה אחרון

def already_sent_recently(symbol, strategy_name, minutes=15):
    key = (symbol, strategy_name)
    now = datetime.utcnow()
    if key in LAST_SIGNALS:
        last_time = LAST_SIGNALS[key]
        if (now - last_time).total_seconds() < minutes * 60:
            return True
    LAST_SIGNALS[key] = now
    return False
def analyze_asset_df(client, symbol, df, signals_df, strategy_func, strategy_name):
    from utils import log_rejection, send_telegram, log_signal  # ✅ השאר ככה

    if df is None or df.empty or len(df) < max(EMA_LONG, VOLUME_LOOKBACK, 25):
        log_rejection(symbol, f"לא מספיק נרות ({strategy_name})")
        return

    print(f"🔍 [{symbol}] כמות נרות שהתקבלו: {len(df)}")

    buy_score, reasons = strategy_func(df)

    threshold = STRATEGY_THRESHOLDS.get(strategy_name, 1)
    if buy_score >= threshold:
        last = df.iloc[-1]
        price_now = last['close']
        atr_value = last.get('atr', 0)
        tp = price_now + (atr_value * 2)
        sl = price_now - ((atr_value * 2) / RISK_REWARD_RATIO)
        expected_profit = abs((tp - price_now) / price_now)

        if expected_profit < EXPECTED_PROFIT_MIN:
            log_rejection(symbol, f"רווח צפוי נמוך: {expected_profit:.2%} ({strategy_name})")
            return

        if already_sent_recently(symbol, strategy_name):
            log_rejection(symbol, "סיגנל זהה כבר נשלח לאחרונה", strategy_name)
            return

        message = (
            f"📈 BUY SIGNAL: {symbol} ({strategy_name})\n"
            f"מחיר: {price_now:.4f} $\n"
            f"TP: {tp:.4f} | SL: {sl:.4f}\n"
            f"סיבות: {' | '.join(reasons)}"
        )
        send_telegram(message)
        log_signal(symbol, price_now, strategy_name, tp, sl)
    else:
        print(f"⚠️ סיבות לדחייה: {' | '.join(reasons)}")
        log_rejection(symbol, f"Buy score נמוך ({buy_score}/{threshold})", strategy_name)