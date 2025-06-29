import pandas as pd
import os
import re
from datetime import datetime
import pytz

def clean_signal_times(df):
    def clean_time_string(t):
        if pd.isna(t):
            return None
        t = str(t).strip()
        t = re.sub(r"[^\d:/\s\-]", "", t)
        for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%Y/%m/%d %H:%M"):
            try:
                return datetime.strptime(t, fmt)
            except:
                continue
        return pd.NaT

    df["time"] = df["time"].apply(clean_time_string)
    df = df.dropna(subset=["time"])
    df["time"] = pd.to_datetime(df["time"]).dt.tz_localize("Asia/Jerusalem")
    return df

def load_signals(signals_path):
    expected_columns = [
        "time", "symbol", "entry_price", "TP", "SL", "strategy", "signal_id",
        "RSI_OVERSOLD", "EMA_SHORT", "EMA_LONG", "VOLUME_LOOKBACK", "VOLATILITY_THRESHOLD",
        "MIN_VOLUME", "INTERVAL", "RISK_REWARD_RATIO", "EXPECTED_PROFIT_MIN, VOLUME"
    ]

    # טען את הקובץ ללא הגדרת כמות עמודות
    df = pd.read_csv(signals_path, header=None, engine="python", on_bad_lines='skip')

    # הוסף עמודות חסרות אם צריך
    while len(df.columns) < len(expected_columns):
        df[len(df.columns)] = None

    # חתוך עמודות עודפות
    if len(df.columns) > len(expected_columns):
        df = df.iloc[:, :len(expected_columns)]

    df.columns = expected_columns
    return clean_signal_times(df)
