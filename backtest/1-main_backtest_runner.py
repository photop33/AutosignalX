import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from load_signals import load_signals
from signal_analyzer import analyze_signal
from convert_new_signal import merge_config_columns
from add_indctor import enrich_signals_with_indicators
from  build_ml_dataset import add_ml_features_to_signals
# 📁 נתיבים
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
signals_path = os.path.join(log_dir, "signals_log.csv")
output_path = os.path.join(log_dir, "signal_backtest_results_full.xlsx")

# 📥 טען את הסיגנלים
signals_df = load_signals(signals_path)

# 🧼 סנן סיגנלים שכבר נותחו


if signals_df.empty:
    print("⚠️ אין סיגנלים חדשים לניתוח.")
else:
    # 🧠 ניתוח הסיגנלים החדשים
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(analyze_signal, [row for _, row in signals_df.iterrows()]))

    results = [r for r in results if r]
    results_df = pd.DataFrame(results)

    # 📌 העבר את signal_id לראש העמודות
    if "signal_id" in results_df.columns:
        cols = ["signal_id"] + [col for col in results_df.columns if col != "signal_id"]
        results_df = results_df[cols]

    # ⏳ הסר אזורי זמן
    for col in ["cross_line_time", "signal_time"]:
        if col in results_df.columns:
            results_df[col] = pd.to_datetime(results_df[col], errors="coerce").dt.tz_localize(None)

    # 🧩 איחוד עם התוצאות הקיימות (אם קיימות)

    # 💾 שמור את הקובץ
    results_df.to_excel(output_path, index=False)
    print(f"✅ נשמר הקובץ: {output_path} | נוספו {len(results)} שורות.")

    # 🧠 שלב אחרון: מיזוג קונפיג לפי signal_id
signals_df, existing_df = merge_config_columns()
if not existing_df.empty:
    results_df = pd.concat([existing_df, results_df], ignore_index=True)
full_input_path = os.path.join(log_dir, "signal_backtest_results_with_indicators.xlsx")
full_output_path = os.path.join(log_dir, "signal_backtest_results_for_AI.xlsx")


# הוסף אינדקטורים נוספים- add_indctor.py
enrich_signals_with_indicators(
    file_path=full_input_path,
    output_path=full_output_path
)

#הכנת הדאטה לפונקציות חחכמות לשימוש ב-AI בקובץ build_ml_dataset
input_path = os.path.join(log_dir, "signal_backtest_results_for_AI.xlsx")
output_path = os.path.join(log_dir, "signal_backtest_results_for_AI.xlsx")
add_ml_features_to_signals(input_path, output_path)


