# ✅ Live Signal Predictor with LightGBM Model + פיצ'רים מלאים
import pandas as pd
import joblib
import ta
from binance.client import Client
from datetime import datetime, timezone
import pytz
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from my_keys import BINANCE_API_KEY, BINANCE_API_SECRET
# --- אתחול Binance
client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)
israel_tz = pytz.timezone("Asia/Jerusalem")

# --- טען מודל מאומן (LightGBM לדוגמה)
MODEL_PATH = os.path.join("..", "models", "lgbm_model.pkl")
model = joblib.load(MODEL_PATH)

# --- פונקציה לקבלת פיצ'רים לעסקה חיה
def get_features_for_signal(symbol):
    try:
        klines = client.get_klines(symbol=symbol, interval="1m", limit=50)
        df = pd.DataFrame(klines, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'])
        df[['high', 'low', 'close', 'volume']] = df[['high', 'low', 'close', 'volume']].astype(float)

        df['rsi'] = ta.momentum.RSIIndicator(close=df['close']).rsi()
        df['macd'] = ta.trend.MACD(close=df['close']).macd()
        df['adx'] = ta.trend.ADXIndicator(high=df['high'], low=df['low'], close=df['close']).adx()
        df['ema_short'] = ta.trend.EMAIndicator(close=df['close'], window=12).ema_indicator()
        df['ema_long'] = ta.trend.EMAIndicator(close=df['close'], window=26).ema_indicator()
        bb = ta.volatility.BollingerBands(close=df['close'])

        last = df.dropna().iloc[-1]

        now = datetime.now(israel_tz)
        volume_avg = df['volume'].rolling(window=20).mean().iloc[-1]
        volatility = (df['high'] - df['low']).rolling(window=20).mean().iloc[-1]
        trend_strength = abs(last['ema_short'] - last['ema_long'])
        bb_width = (bb.bollinger_hband() - bb.bollinger_lband()).iloc[-1]

        # מיפוי קטגוריה
        symbol_category_map = {
            "BTCUSDT": "BTC",
            "ETHUSDT": "ALT",
            "SOLUSDT": "ALT",
            "TSLA": "STOCK",
            "AAPL": "STOCK"
        }
        symbol_category = symbol_category_map.get(symbol, "OTHER")
        category_encoded = {"BTC": 0, "ALT": 1, "STOCK": 2, "OTHER": 3}[symbol_category]

        trend_ema = int(last['ema_short'] > last['ema_long'])

        features = pd.DataFrame([{
            'RSI': round(last['rsi'], 2),
            'MACD': round(last['macd'], 4),
            'ADX': round(last['adx'], 2),
            'hour': now.hour,
            'day_of_week': now.weekday(),
            'trend_ema': trend_ema,
            'Volume_avg': round(volume_avg, 2),
            'Volatility': round(volatility, 4),
            'Trend_strength': round(trend_strength, 4),
            'BB_width': round(bb_width, 4),
            'Symbol_category': category_encoded,
            # אם השתמשת גם ב-'symbol' או 'strategy' יש למפות גם אותם כאן לפי LabelEncoder המתאים
        }])

        return features

    except Exception as e:
        print(f"❌ שגיאה בקבלת פיצ'רים עבור {symbol}: {e}")
        return None

# --- תחזית חיה
def predict_success(symbol):
    features = get_features_for_signal(symbol)
    if features is None:
        return "❌ לא ניתן לחזות"

    prob = model.predict_proba(features)[0][1]
    status = "✅ גבוהה" if prob > 0.8 else "⚠️ בינונית/נמוכה"
    return f"סיכוי הצלחה: {round(prob * 100, 2)}% ({status})"

# --- בדיקת דוגמה
if __name__ == "__main__":
    symbol = "BTCUSDT"
    print(f"📊 {symbol} → {predict_success(symbol)}")
