# 📄 pages/2_Analysis.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np

st.set_page_config(page_title="📈 ניתוח אסטרטגיות", layout="wide")
st.title("📈 ניתוח רווח מצטבר לפי אסטרטגיה")

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
    df['date'] = df['signal_time'].dt.date

st.sidebar.header("📂 סינון אסטרטגיות")
selected_strategy = st.sidebar.multiselect("בחר אסטרטגיות:", sorted(df['strategy'].dropna().unique()), default=None)
date_range = st.sidebar.date_input("טווח תאריכים:", [])

if selected_strategy:
    df = df[df['strategy'].isin(selected_strategy)]
if len(date_range) == 2:
    df = df[(df['date'] >= date_range[0]) & (df['date'] <= date_range[1])]

# טבלת רווח לפי אסטרטגיה
st.subheader("📊 טבלת רווח לפי אסטרטגיה")
df['TP_HIT'] = df['תוצאה'] == '✅ TP Hit'
summary = df.groupby("strategy").agg(
    מספר_עסקאות=('strategy', 'count'),
    רווח_מצטבר=('PnL_%', 'sum'),
    רווח_ממוצע=('PnL_%', 'mean'),
    סטייה_תקן=('PnL_%', 'std'),
    אחוז_הצלחה=('TP_HIT', 'mean')
).sort_values(by="רווח_מצטבר", ascending=False)
summary['אחוז_הצלחה'] = summary['אחוז_הצלחה'] * 100
st.dataframe(summary, use_container_width=True)

# גרף רווח מצטבר לפי אסטרטגיה עם צבע מדורג
st.subheader("📈 גרף רווח מצטבר לפי אסטרטגיה")
strategy_pnl = df.groupby('strategy')['PnL_%'].sum().reset_index().sort_values(by='PnL_%', ascending=False)
fig = px.bar(
    strategy_pnl,
    x='strategy',
    y='PnL_%',
    color='PnL_%',
    color_continuous_scale='RdYlGn',
    labels={'strategy': 'אסטרטגיה', 'PnL_%': 'רווח מצטבר (%)'},
    title='רווח מצטבר לפי אסטרטגיה'
)
st.plotly_chart(fig, use_container_width=True)

# גרף הצלחות מול כישלונות לכל אסטרטגיה
st.subheader("🔹 פילוח הצלחות וכישלונות לפי אסטרטגיה")
result_counts = df.groupby(['strategy', 'תוצאה']).size().reset_index(name='count')
fig2 = px.bar(
    result_counts,
    x='strategy',
    y='count',
    color='תוצאה',
    barmode='stack',
    title='פילוח הצלחה/כשלון לפי אסטרטגיה'
)
st.plotly_chart(fig2, use_container_width=True)

# גרף רווח מצטבר לאורך זמן לכל אסטרטגיה
st.subheader("🕰️ רווח לפי אסטרטגיה לאורך זמן")
df_sorted = df.sort_values('signal_time')
df_sorted['cumulative_pnl'] = df_sorted.groupby('strategy')['PnL_%'].cumsum()
fig3 = px.line(
    df_sorted,
    x='signal_time',
    y='cumulative_pnl',
    color='strategy',
    labels={'cumulative_pnl': 'רווח מצטבר', 'signal_time': 'זמן'},
    title='מגמה רווח לפי אסטרטגיות לאורך הזמן'
)
st.plotly_chart(fig3, use_container_width=True)