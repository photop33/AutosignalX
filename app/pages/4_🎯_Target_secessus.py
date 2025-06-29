# 📄 pages/3_Contextual_Filter.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="🎯 פילוח הצלחות לפי תנאי שוק", layout="wide")
st.title("🎯 פילוח הצלחות לפי תנאי שוק")

FILE_NAME = os.path.join("..", "logs", "signal_backtest_results_for_AI.xlsx")
if not os.path.exists(FILE_NAME):
    st.warning(f"הקובץ {FILE_NAME} לא נמצא")
    st.stop()

try:
    df = pd.read_excel(FILE_NAME)
except Exception as e:
    st.error(f"שגיאה בטעינת הקובץ: {e}")
    st.stop()

if 'signal_time' in df.columns:
    df['signal_time'] = pd.to_datetime(df['signal_time'])
    df['hour'] = df['signal_time'].dt.hour
    df['day_of_week'] = df['signal_time'].dt.day_name()

# תנאים מקדימים
st.sidebar.header("📂 תנאי סינון")
atrs = st.sidebar.slider("ADX בין:", float(df['ADX'].min()), float(df['ADX'].max()), (float(df['ADX'].min()), float(df['ADX'].max())))
rsi_range = st.sidebar.slider("RSI בין:", 0, 100, (0, 100))
ema_condition = st.sidebar.selectbox("בחר מצב EMA:", ["הכל", "EMA קצר מעל ארוך", "EMA קצר מתחת לארוך"])

# סינון נתונים
filtered_df = df[(df['ADX'] >= atrs[0]) & (df['ADX'] <= atrs[1])]
filtered_df = filtered_df[(filtered_df['RSI'] >= rsi_range[0]) & (filtered_df['RSI'] <= rsi_range[1])]

if ema_condition == "EMA קצר מעל ארוך":
    filtered_df = filtered_df[filtered_df['ema_short'] > filtered_df['ema_long']]
elif ema_condition == "EMA קצר מתחת לארוך":
    filtered_df = filtered_df[filtered_df['ema_short'] < filtered_df['ema_long']]

# אחוז הצלחות
filtered_df['TP_HIT'] = filtered_df['תוצאה'] == '✅ TP Hit'
success_rate = filtered_df['TP_HIT'].mean() * 100 if not filtered_df.empty else 0

st.metric("✅ אחוז הצלחות בתנאים הנבחרים", f"{success_rate:.2f}%")

st.dataframe(filtered_df[['symbol', 'strategy', 'ADX', 'RSI', 'ema_short', 'ema_long', 'תוצאה']])
