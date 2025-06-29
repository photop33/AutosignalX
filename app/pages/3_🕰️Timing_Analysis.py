# 📄 pages/3_Timing_Analysis.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="🕒 ניתוח זמנים", layout="wide")
st.title("🕒 ניתוח הצלחות לפי ימים ושעות")

FILE_NAME = os.path.join("..", "logs", "signal_backtest_results_for_AI.xlsx")
if not os.path.exists(FILE_NAME):
    st.warning(f"הקובץ {FILE_NAME} לא נמצא")
    st.stop()

df = pd.read_excel(FILE_NAME)
df['signal_time'] = pd.to_datetime(df['signal_time'])
df['date'] = df['signal_time'].dt.date
df['weekday'] = df['signal_time'].dt.day_name()
df['hour'] = df['signal_time'].dt.hour
df['TP_HIT'] = df['תוצאה'] == '✅ TP Hit'

# 🟢 אחוז הצלחות לפי יום
day_summary = df.groupby('weekday')['TP_HIT'].mean().reset_index()
day_summary['TP_HIT'] *= 100
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_summary['weekday'] = pd.Categorical(day_summary['weekday'], categories=day_order, ordered=True)
day_summary = day_summary.sort_values('weekday')

st.subheader("📅 אחוז הצלחות לפי יום בשבוע")
fig_day = px.bar(
    day_summary,
    x='weekday',
    y='TP_HIT',
    labels={'weekday': 'יום', 'TP_HIT': 'אחוז הצלחות (%)'},
    color='TP_HIT',
    color_continuous_scale='RdYlGn'
)
st.plotly_chart(fig_day, use_container_width=True)

# 🕐 אחוז הצלחות לפי שעה
hour_summary = df.groupby('hour')['TP_HIT'].mean().reset_index()
hour_summary['TP_HIT'] *= 100

st.subheader("⏰ אחוז הצלחות לפי שעה")
fig_hour = px.bar(
    hour_summary,
    x='hour',
    y='TP_HIT',
    labels={'hour': 'שעה', 'TP_HIT': 'אחוז הצלחות (%)'},
    color='TP_HIT',
    color_continuous_scale='RdYlGn'
)
st.plotly_chart(fig_hour, use_container_width=True)

# 🔥 Heatmap לפי יום ושעה
heatmap_data = df.groupby(['weekday', 'hour'])['TP_HIT'].mean().reset_index()
heatmap_data['TP_HIT'] *= 100
heatmap_data['weekday'] = pd.Categorical(heatmap_data['weekday'], categories=day_order, ordered=True)

st.subheader("🌡️ Heatmap של אחוז הצלחה לפי יום ושעה")
fig_heatmap = px.density_heatmap(
    heatmap_data,
    x='hour',
    y='weekday',
    z='TP_HIT',
    color_continuous_scale='RdYlGn',
    labels={'hour': 'שעה', 'weekday': 'יום', 'TP_HIT': 'אחוז הצלחות (%)'},
    nbinsx=24
)
st.plotly_chart(fig_heatmap, use_container_width=True)
