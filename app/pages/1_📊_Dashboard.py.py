import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

st.set_page_config(page_title="📊 Crypto Trading Dashboard", layout="wide")
st.title("📈 לוח בקרה למסחר יומי בקריפטו")

# טען את קובץ האקסל
FILE_NAME = os.path.join("..", "logs", "signal_backtest_results_for_AI.xlsx")
if not os.path.exists(FILE_NAME):
    st.warning(f"הקובץ {FILE_NAME} לא נמצא")
    st.stop()

# טען נתונים
try:
    df = pd.read_excel(FILE_NAME)
except Exception as e:
    st.error(f"שגיאה בטעינת הקובץ: {e}")
    st.stop()

# המרות סוגי נתונים
if 'signal_time' in df.columns:
    df['signal_time'] = pd.to_datetime(df['signal_time'])
    df['date'] = df['signal_time'].dt.date

# פילטרים צדדיים
st.sidebar.header("📂 סינון")
selected_symbol = st.sidebar.multiselect("בחר מטבעות:", sorted(df['symbol'].unique()), default=None)
selected_result = st.sidebar.multiselect("בחר תוצאה:", ["✅ TP Hit", "❌ SL Hit", "⏳ Still Open"], default=None)
date_range = st.sidebar.date_input("טווח תאריכים:", [])
selected_strategy = st.sidebar.multiselect("בחר אסטרטגיות:", sorted(df['strategy'].dropna().unique()), default=None)


# סינון בפועל
filtered_df = df.copy()
if selected_symbol:
    filtered_df = filtered_df[filtered_df['symbol'].isin(selected_symbol)]
if selected_result:
    filtered_df = filtered_df[filtered_df['תוצאה'].isin(selected_result)]
if len(date_range) == 2:
    filtered_df = filtered_df[(filtered_df['date'] >= date_range[0]) & (filtered_df['date'] <= date_range[1])]
if selected_strategy:
    filtered_df = filtered_df[filtered_df['strategy'].isin(selected_strategy)]

# כרטיסים סטטיסטיים
#דשה 1
col1, col2, col3 = st.columns(3)
col1.metric("📌 סך העסקאות", len(filtered_df))
# שדה 2
closed_df = filtered_df[filtered_df['תוצאה'].isin(['✅ TP Hit', '❌ SL Hit'])]
tp_count = closed_df['תוצאה'].value_counts().get('✅ TP Hit', 0)
total_closed = len(closed_df)

success_rate = (tp_count / total_closed) * 100 if total_closed > 0 else 0

col2.metric("✅ אחוז הצלחות (TP)", f"{success_rate:.1f}%")
closed_trades = filtered_df[filtered_df['תוצאה'].isin(['✅ TP Hit', '❌ SL Hit'])]

#שדה 3
col3.metric("💸 רווח/הפסד נטו", f"{filtered_df['PnL_%'].sum():.2f}%")
#שדה 4
# חישוב רווח נטו לפי אסטרטגיה
strategy_pnl = filtered_df.groupby('strategy')['PnL_%'].sum().sort_values(ascending=False)

if not strategy_pnl.empty:
    best_strategy = strategy_pnl.idxmax()
    best_profit = strategy_pnl.max()
    st.metric("🥇 האסטרטגיה הכי רווחית", f"{best_strategy} ({best_profit:.2f}%)")
else:
    st.metric("🥇 האסטרטגיה הכי רווחית", "אין נתונים")





# מפה מותאמת של צבעים לפי תוצאה
color_map = {
    '✅ TP Hit': '#2ecc71',     # ירוק חלק
    '❌ SL Hit': '#e74c3c',     # אדום עמוק
    '⏳ Still Open': '#95a5a6'  # אפור נקי
}

# גרף הצלחות לפי תאריך עם צבעים מותאמים

fig1 = px.histogram(
    filtered_df,
    x='date',
    color='תוצאה',
    barmode='group',
    color_discrete_map=color_map,
    title="📊 פיזור עסקאות לפי תוצאה"
)

fig1.update_layout(
    title_font=dict(size=20, family="Arial", color="black"),
    xaxis_title="תאריך",
    yaxis_title="כמות עסקאות",
    plot_bgcolor='white',
    paper_bgcolor='white',
    legend=dict(title="תוצאה", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig1, use_container_width=True)


# טבלה מלאה
st.subheader("📋 טבלת עסקאות")
st.dataframe(filtered_df.sort_values(by='signal_time', ascending=False).reset_index(drop=True), use_container_width=True)

# הורדת קובץ Excel
output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    filtered_df.to_excel(writer, index=False)
output.seek(0)

st.download_button(
    label="📥 הורד כ-Excel",
    data=output,
    file_name="filtered_trades.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
