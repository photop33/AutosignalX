import pandas as pd
import numpy as np
import os

def add_ml_features_to_signals(input_excel_path: str, output_excel_path: str):
    # טען את הקובץ
    try:
        df = pd.read_excel(input_excel_path, sheet_name=0)
    except FileNotFoundError:
        raise FileNotFoundError(f"קובץ לא נמצא: {input_excel_path}")

    # המרה לזמן אם קיים
    for col in ["signal_time", "cross_line_time"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # 1. תוספת שעה ויום מהזמן שנשלח הסיגנל
    if "signal_time" in df.columns:
        df["hour_of_day"] = df["signal_time"].dt.hour.fillna(-1).astype(int)
        df["day_of_week"] = df["signal_time"].dt.dayofweek.fillna(-1).astype(int)

    # 2. חישוב זמן בשניות מהסיגנל עד TP/SL
    if {"cross_line_time", "signal_time"}.issubset(df.columns):
        df["tp_sl_duration_sec"] = (df["cross_line_time"] - df["signal_time"]).dt.total_seconds()

    # 3. המרחק ל-TP ו-SL באחוזים
    if {"entry_price", "TL", "SL"}.issubset(df.columns):
        df["tp_pct"] = ((df["TL"] - df["entry_price"]) / df["entry_price"]).round(4)
        df["sl_pct"] = ((df["entry_price"] - df["SL"]) / df["entry_price"]).round(4)

    # 4. יחס סיכוי סיכון בפועל
    if {"tp_pct", "sl_pct"}.issubset(df.columns):
        df["rr_ratio_actual"] = (df["tp_pct"] / df["sl_pct"]).replace([np.inf, -np.inf], np.nan).round(2)

    # 5. MACD Histogram = MACD - Signal
    if {"macd", "macd_signal"}.issubset(df.columns):
        df["macd_hist"] = (df["macd"] - df["macd_signal"]).round(5)

    # 6. תנודתיות יחסית = bb_width / entry_price
    if {"bb_width", "entry_price"}.issubset(df.columns):
        df["volatility_normalized"] = (df["bb_width"] / df["entry_price"]).replace([np.inf, -np.inf], np.nan).round(5)

    # שמור לקובץ חדש
    df.to_excel(output_excel_path, index=False)
    print(f"✅ נוספו מאפיינים חכמים ונשמרו בקובץ החדש: {output_excel_path}")

# שימוש בדוגמה:
if __name__ == "__main__":
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    input_path = os.path.join(log_dir, "signal_backtest_results_for_AI.xlsx")
    output_path = os.path.join(log_dir, "signal_backtest_results_for_AI.xlsx")
