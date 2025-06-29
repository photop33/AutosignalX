# 📄 pages/7_Model_Comparison.py
import streamlit as st
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import LabelEncoder
import lightgbm as lgb
import xgboost as xgb
import catboost as cb
import plotly.graph_objects as go

st.set_page_config(page_title="🤖 השוואת מודלים", layout="wide")
st.title("🤖 השוואת מודלים: LightGBM, XGBoost, CatBoost")

FILE_NAME = os.path.join("..", "logs", "signal_backtest_results_for_AI.xlsx")
if not os.path.exists(FILE_NAME):
    st.warning(f"הקובץ {FILE_NAME} לא נמצא")
    st.stop()

try:
    df = pd.read_excel(FILE_NAME)
except Exception as e:
    st.error(f"שגיאה בטעינת הקובץ: {e}")
    st.stop()

# עיבוד זמן
if 'signal_time' in df.columns:
    df['signal_time'] = pd.to_datetime(df['signal_time'])
    df['hour'] = df['signal_time'].dt.hour
    df['day_of_week'] = df['signal_time'].dt.dayofweek

# הצלחה: ✅ TP Hit בלבד
valid_results = ['✅ TP Hit', '❌ SL Hit']
df = df[df['תוצאה'].isin(valid_results)]
df['success'] = df['תוצאה'] == '✅ TP Hit'

# Label Encoding לקטגוריות
encoders = {}
for col in ['symbol', 'strategy', 'Symbol_category']:
    if col in df.columns:
        enc = LabelEncoder()
        df[col] = enc.fit_transform(df[col].astype(str))
        encoders[col] = enc

# תנאי מגמה EMA
if 'ema_short' in df.columns and 'ema_long' in df.columns:
    df['trend_ema'] = (df['ema_short'] > df['ema_long']).astype(int)

# תכונות
feature_cols = [col for col in [
    'RSI', 'MACD', 'ADX', 'hour', 'day_of_week',
    'symbol', 'strategy', 'trend_ema',
    'Volume_avg', 'Volatility', 'Trend_strength', 'BB_width', 'Symbol_category']
    if col in df.columns]

if not feature_cols:
    st.error("לא נמצאו מספיק עמודות חיזוי")
    st.stop()

# הכנת דאטה
model_df = df.dropna(subset=feature_cols + ['success'])
X = model_df[feature_cols]
y = model_df['success']

# חלוקה לסטים
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# פונקציה לאימון והערכה
results = {}

def evaluate_model(name, model):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    report = classification_report(y_test, y_pred, output_dict=True)
    auc = roc_auc_score(y_test, y_proba)
    results[name] = {
        'accuracy': report['accuracy'],
        'auc': auc,
        'precision': report['True']['precision'],
        'recall': report['True']['recall'],
        'f1': report['True']['f1-score']
    }

# השוואת מודלים
with st.spinner("מאמן מודלים..."):
    evaluate_model("LightGBM", lgb.LGBMClassifier())
    evaluate_model("XGBoost", xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss'))
    evaluate_model("CatBoost", cb.CatBoostClassifier(verbose=0))

# תצוגה גרפית
st.subheader("📊 השוואת ביצועים")
metrics = ['accuracy', 'auc', 'precision', 'recall', 'f1']
fig = go.Figure()

for metric in metrics:
    fig.add_trace(go.Bar(
        x=list(results.keys()),
        y=[results[model][metric] for model in results],
        name=metric
    ))

fig.update_layout(barmode='group', title="השוואת מודלים לפי מדדים", xaxis_title="מודל", yaxis_title="ערך")
st.plotly_chart(fig, use_container_width=True)

# טבלת תוצאות
st.subheader("📋 טבלה מסכמת")
st.dataframe(pd.DataFrame(results).T.round(3))
