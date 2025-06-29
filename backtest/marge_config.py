import pandas as pd
import os

def merge_config_snapshot_into_results():
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    results_path = os.path.join(log_dir, "signal_backtest_results_with_indicators.xlsx")
    snapshot_path = os.path.join(log_dir, "signals_log_snapshot.csv")

    # טען את הקבצים
    results_df = pd.read_excel(results_path)
    snapshot_df = pd.read_csv(snapshot_path)

    if "signal_id" not in results_df.columns or "signal_id" not in snapshot_df.columns:
        print("❌ עמודת signal_id לא נמצאה באחד הקבצים")
        return

    # רק עמודות הקונפיג למיזוג
    config_columns = [
        "RSI_OVERSOLD", "EMA_SHORT", "EMA_LONG", "VOLUME_LOOKBACK",
        "VOLATILITY_THRESHOLD", "MIN_VOLUME", "INTERVAL",
        "RISK_REWARD_RATIO", "EXPECTED_PROFIT_MIN"
    ]

    columns_to_merge = ["signal_id"] + config_columns
    snapshot_df = snapshot_df[columns_to_merge]

    # מיזוג לפי signal_id
    merged_df = pd.merge(results_df, snapshot_df, on="signal_id", how="left")

    # שמור את הקובץ המעודכן
    merged_df.to_excel(results_path, index=False)
    print(f"✅ נוספו ערכי קונפיג לכל שורה לפי signal_id ונשמר לקובץ: {results_path}")
