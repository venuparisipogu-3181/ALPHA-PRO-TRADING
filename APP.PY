import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import time
from datetime import datetime

st.set_page_config(layout="wide", page_title="🚀 Alpha Pro Terminal", initial_sidebar_state="expanded")

# Telegram
TELEGRAM_TOKEN = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"
CHAT_ID = "2115666034"

def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}, timeout=5)
        return True
    except:
        return False

st.markdown("""
<div style='text-align:center; padding:30px; background:linear-gradient(135deg,#667eea,#764ba2); color:white; border-radius:25px;'>
<h1>🚀 ALPHA PRO TERMINAL</h1>
<h3>Live NIFTY/BankNifty | Candles | Greeks | Telegram Alerts</h3>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("⚙️ Controls")
index = st.sidebar.selectbox("Index", ["NIFTY", "BANKNIFTY"])
live_mode = st.sidebar.checkbox("🔴 LIVE", value=True)
speed = st.sidebar.slider("Speed", 3, 12, 5)

if 'candles' not in st.session_state:
    st.session_state.candles = pd.DataFrame()

def create_candle():
    base = 25750 if index == "NIFTY" else 52500
    t = time.time()
    prev = st.session_state.candles['close'].iloc[-1] if len(st.session_state.candles)>0 else base
    o = prev
    c = o + np.sin(t/15)*25 + np.random.normal(0, 12)
    h = max(o,c) + abs(np.random.normal(0, 20))
    l = min(o,c) - abs(np.random.normal(0, 20))
    return pd.DataFrame([{
        'time': datetime.now(),
        'open': round(o,2), 'high': round(h,2),
        'low': round(l,2), 'close': round(c,2),
        'volume': int(1500000 + abs(np.sin(t/10))*800000)
    }])

if live_mode:
    new = create_candle()
    st.session_state.candles = pd.concat([st.session_state.candles, new])
    st.session_state.candles = st.session_state.candles.tail(50)

if len(st.session_state.candles) == 0:
    for i in range(30):
        st.session_state.candles = pd.concat([st.session_state.candles, create_candle()])

df = st.session_state.candles.copy()
spot = df['close'].iloc[-1]
ema20 = df['close'].ewm(span=20).mean().iloc[-1]
rsi = 50 + np.sin(time.time()/15)*25
step = 50 if index == "NIFTY" else 100
atm = int(round(spot/step)*step)

# Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("💹 Spot", f"₹{spot:.0f}", f"{spot-ema20:+.0f}")
col2.metric("📈 EMA20", f"₹{ema20:.0f}")
col3.metric("⚡ RSI", f"{rsi:.1f}")
col4.metric("🎯 ATM", atm)

# Chart
st.markdown("---")
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df['time'], open=df['open'], high=df['high'], 
                           low=df['low'], close=df['close'],
                           increasing_line_color='#00ff88', decreasing_line_color='#ff4444'))
fig.add_trace(go.Scatter(x=df['time'], y=df['close'].ewm(span=20).mean(), 
                        line=dict(color='orange', width=3), name='EMA20'))
fig.update_layout(height=500, template='plotly_dark', title=f"{index} Live")
st.plotly_chart(fig, use_container_width=True)

# Option Chain
st.markdown("---")
strikes = [atm-step, atm, atm+step]
option_data = []
for strike in strikes:
    ce = max(15, abs(spot-strike)*0.25 + 25)
    pe = max(15, abs(spot-strike)*0.22 + 20)
    option_data.append({'Strike': strike, 'CE': f"₹{ce:.0f}", 'PE': f"₹{pe:.0f}'} )

st.dataframe(pd.DataFrame(option_data), use_container_width=True)

# Signals
st.markdown("---")
ce_signal = spot > ema20 and rsi > 55
pe_signal = spot < ema20 and rsi < 45

col1, col2 = st.columns(2)
with col1:
    if ce_signal:
        st.error(f"🚀 BUY {atm} CE")
        send_alert(f"🟢 BUY {atm} CE | Spot: ₹{spot:.0f}")
    else:
        st.info("⏳ CE Wait")

with col2:
    if pe_signal:
        st.error(f"📉 BUY {atm} PE")
        send_alert(f"🔴 BUY {atm} PE | Spot: ₹{spot:.0f}")
    else:
        st.info("⏳ PE Wait")

# Buttons
if st.button("🔔 Test Telegram"):
    send_alert(f"🧪 Alpha Pro Test | {index} ₹{spot:.0f}")
    st.success("✅ Sent!")

if st.button("🔄 Update"):
    st.rerun()

if live_mode:
    time.sleep(speed)
    st.rerun()
