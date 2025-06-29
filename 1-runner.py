from binance.client import Client
from concurrent.futures import ThreadPoolExecutor
from analyzer import analyze_asset_df
from config import *
from data_loader import load_signals
from indicators import compute_indicators
from utils import get_klines
import time
from tqdm import tqdm
import importlib

client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)
signals_df = load_signals()

# מספר קבוצות שנסרקות ברוטציה
NUM_BATCHES = 4
BATCH_SIZE = 300
current_batch_index = 0  # משתנה שיזכור איזו קבוצה תסרק

def get_volatile_symbols():
    tickers = client.get_ticker()
    symbols = []
    for t in tickers:
        symbol = t['symbol']
        if any(symbol.endswith(base) for base in ['USDT', 'FDUSD', 'USDC', 'TUSD']):
            try:
                change = float(t['priceChangePercent']) / 100
                volume = float(t['quoteVolume'])
                if change > 0 and abs(change) >= VOLATILITY_THRESHOLD and volume >= MIN_VOLUME:
                    symbols.append(symbol)
            except:
                continue
    return sorted(symbols)  # כדי שתמיד הסדר יהיה אחיד

while True:
    start_time = time.time()  # 🕒 תחילת זמן הסיבוב

    print("\n🚀 התחלת סריקה על כל האסטרטגיות")

    all_symbols = get_volatile_symbols()
    total = len(all_symbols)
    print(f"📈 נמצאו {total} מטבעות תנודתיים")

    scanned_any = False  # דגל האם סרקנו לפחות קבוצה אחת עם מטבעות

    for i in range(NUM_BATCHES):
        current_batch_index = (current_batch_index + 1) % NUM_BATCHES

        start = current_batch_index * BATCH_SIZE
        end = start + BATCH_SIZE
        crypto_symbols = all_symbols[start:end]
        print(f"🔄 מריץ קבוצה {current_batch_index + 1}/{NUM_BATCHES} ({len(crypto_symbols)} מטבעות)")

        if not crypto_symbols:
            print("⏭️ אין מטבעות לסרוק בקבוצה זו, עובר מיידית לקבוצה הבאה...")
            continue

        scanned_any = True  # סימון שסרקנו

        # שלב 1: משוך נתונים
        symbol_data = {}
        for symbol in crypto_symbols:
            df = get_klines(client, symbol, INTERVAL)
            if not df.empty:
                df = compute_indicators(df)
                symbol_data[symbol] = df

        # שלב 2: הרץ אסטרטגיות
        for strategy_name in ACTIVE_STRATEGIES:
            try:
                strategy_module = importlib.import_module(f"strategies.{strategy_name}")
                strategy_func = getattr(strategy_module, strategy_name)

                print(f"\n📊 מריץ אסטרטגיה: {strategy_name}")
                with ThreadPoolExecutor(max_workers=2) as executor:
                    list(tqdm(executor.map(
                        lambda s: analyze_asset_df(client, s, symbol_data[s], signals_df, strategy_func, strategy_name),
                        crypto_symbols),
                        total=len(crypto_symbols)))

            except Exception as e:
                print(f"❌ שגיאה באסטרטגיה {strategy_name}: {e}")

    # ✅ המתן עד לדקה הבאה רק אם סרקנו משהו
    if scanned_any:
        elapsed = time.time() - start_time
        sleep_time = max(0, 60 - elapsed)
        print(f"⌛ מחכה {int(sleep_time)} שניות עד הסיבוב הבא...")
        time.sleep(sleep_time)
    else:
        print("⚠️ לא סרקנו כלום, מריץ סיבוב נוסף מיד...")
