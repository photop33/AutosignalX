import pandas as pd
import os

def merge_config_columns():
    # נתיבים
    base_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    log_csv = os.path.join(base_dir, "signals_log.csv")
    output_xlsx = os.path.join(base_dir, "signal_backtest_results_with_indicators.xlsx")

    # שמות העמודות בקובץ signals_log
    full_columns = [
        "time", "symbol", "entry_price", "TP", "SL", "strategy", "signal_id",
        "RSI_OVERSOLD", "EMA_SHORT", "EMA_LONG", "VOLUME_LOOKBACK",
        "VOLATILITY_THRESHOLD", "MIN_VOLUME", "INTERVAL",
        "RISK_REWARD_RATIO", "EXPECTED_PROFIT_MIN"
    ]

    # טען את שני הקבצים
    log_df = pd.read_csv(log_csv, header=None, names=full_columns, engine="python", on_bad_lines="skip")

    if os.path.exists(output_xlsx):
        results_df = pd.read_excel(output_xlsx)
    else:
        results_df = pd.DataFrame()

    # שמות העמודות שרוצים להוסיף
    config_columns = full_columns[7:]  # עמודות H-Q (indexes 7-15)

    # ודא שהעמודות קיימות ב־results_df
    for col in config_columns:
        if col not in results_df.columns:
            results_df[col] = None

    # מיזוג לפי signal_id
    merged_df = results_df.merge(
        log_df[["signal_id"] + config_columns],
        on="signal_id",
        how="left",
        suffixes=('', '_from_log')
    )

    # עדכון הערכים בעמודות הקונפיג
    for col in config_columns:
        if col + "_from_log" in merged_df.columns:
            merged_df[col] = merged_df[col].combine_first(merged_df[col + "_from_log"])
            merged_df.drop(columns=[col + "_from_log"], inplace=True)

    # שמור את הקובץ
    merged_df.to_excel(output_xlsx, index=False)
    print(f"✅ עמודות הקונפיג הועתקו לפי signal_id ונשמרו ל: {output_xlsx}")

    # החזר מידע חיוני לפעולה הראשית
    existing_ids = set(merged_df["signal_id"]) if not merged_df.empty else set()
    new_signals_df = log_df[~log_df["signal_id"].isin(existing_ids)]

    return new_signals_df, merged_df
