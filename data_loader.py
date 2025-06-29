import pandas as pd
import os
# def load_backtest():
#     try:
#         return pd.read_excel("signal_backtest_results_with_pnl.xlsx")
#     except:
#         return pd.DataFrame()

def load_signals():
    path = os.path.join("logs", "signals_log.csv")
    try:
        df = pd.read_csv(
            path,
            header=None,
            names=["datetime", "symbol", "signal", "price"],
            engine="python",           # מנוע גמיש יותר
            on_bad_lines="skip"        # ידלג על שורות בעייתיות
        )
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime", "symbol", "signal", "price"])  # נקה שורות לא תקינות
        return df
    except Exception as e:
        print(f"שגיאה בטעינת signals_log.csv מתוך backtest: {e}")
        return pd.DataFrame(columns=["datetime", "symbol", "signal", "price"])

