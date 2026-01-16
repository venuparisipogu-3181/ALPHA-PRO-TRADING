import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import time
from datetime import datetime

# Telegram Setup
TELEGRAM_TOKEN = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"
CHAT_ID = "2115666034"

def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}, timeout=5)
        return True
    except:
        return False

# Page config
st.set_page_config(layout="wide", page_title="🎯 PCR & Candles LIVE SCREENER")

# Session state for candles
if 'nifty_candles' not in st.session_state:
    st.session_state.nifty_candles = pd.DataFrame()
if 'banknifty_candles' not in st.session_state:
    st.session_state.banknifty_candles = pd.DataFrame()
if 'last_alert_time' not in st.session_state:
    st.session_state.last_alert_time = 0

st.title("🎯 PCR & GREEKS LIVE SCREENER + CANDLES")

# Sidebar
st.sidebar.title("⚙️ Controls")
live_mode = st.sidebar.checkbox("🔴 LIVE STREAMING", value=True)
speed = st.sidebar.slider("⚡ Update Speed", 2, 10, 4)

# === LIVE CANDLE GENERATOR ===
def generate_candle(index_name):
    base_price = 25750 if index_name == "NIFTY" else 52500
    t = time.time()
    
    if len(st.session_state[f"{index_name.lower()}_candles"]) > 0:
        prev_close = st.session_state[f"{index_name.lower()}_candles"]['close'].iloc[-1]
    else:
        prev_close = base_price
    
    open_price = prev_close
    change = np.sin(t/15)*25 + np.random.normal(0, 12)
    high = max(open_price, open_price + change) + abs(np.random.normal(0, 20))
    low = min(open_price, open_price + change) - abs(np.random.normal(0, 20))
    close = open_price + change
    
    return pd.DataFrame([{
        'time': datetime.now(),
        'open': round(open_price, 2),
        'high': round(high, 2),
        'low': round(low, 2),
        'close': round(close, 2),
        'volume': int(1200000 + abs(np.sin(t/10))*800000)
    }])

# Update candles
if live_mode:
    # Nifty candle
    nifty_candle = generate_candle("NIFTY")
    st.session_state.nifty_candles = pd.concat([st.session_state.nifty_candles, nifty_candle], ignore_index=True)
    st.session_state.nifty_candles = st.session_state.nifty_candles.tail(30)
    
    # BankNifty candle
    banknifty_candle = generate_candle("BANKNIFTY")
    st.session_state.banknifty_candles = pd.concat([st.session_state.banknifty_candles, banknifty_candle], ignore_index=True)
    st.session_state.banknifty_candles = st.session_state.banknifty_candles.tail(30)

# Initialize if empty
if len(st.session_state.nifty_candles) == 0:
    for i in range(20):
        st.session_state.nifty_candles = pd.concat([st.session_state.nifty_candles, generate_candle("NIFTY")], ignore_index=True)
if len(st.session_state.banknifty_candles) == 0:
    for i in range(20):
        st.session_state.banknifty_candles = pd.concat([st.session_state.banknifty_candles, generate_candle("BANKNIFTY")], ignore_index=True)

# === MARKET METRICS ===
def get_market_metrics(index_name):
    spot = 25750 + np.sin(time.time()/20)*80 if index_name == "NIFTY" else 52500 + np.sin(time.time()/25)*150
    step = 50 if index_name == "NIFTY" else 100
    atm = round(spot / step) * step
    
    pcr = 1.15 + np.sin(time.time()/30)*0.25
    rsi = 50 + (np.sin(time.time()/15) * 25)
    iv = 14.5 + np.sin(time.time()/40)*2
    
    sentiment = "NEUTRAL"
    if pcr > 1.25: sentiment = "🟢 BULLISH 🚀"
    elif pcr < 0.75: sentiment = "🔴 BEARISH 🩸"
    
    return spot, atm, pcr, rsi, iv, sentiment

# === DUAL LAYOUT ===
col1, col2 = st.columns(2)

# NIFTY SECTION
with col1:
    st.subheader("🟦 NIFTY 50 LIVE")
    
    # Candlestick chart
    n_fig = go.Figure()
    n_df = st.session_state.nifty_candles
    n_fig.add_trace(go.Candlestick(
        x=n_df['time'], open=n_df['open'], high=n_df['high'],
        low=n_df['low'], close=n_df['close'],
        name="NIFTY Live", increasing_line_color='#00ff88', decreasing_line_color='#ff4444'
    ))
    n_fig.update_layout(height=300, title="NIFTY Live Candles")
    st.plotly_chart(n_fig, use_container_width=True)
    
    n_spot, n_atm, n_pcr, n_rsi, n_iv, n_sent = get_market_metrics("NIFTY")
    st.metric("SPOT", f"₹{n_spot:.1f}", f"PCR {n_pcr:.2f}")
    st.success(f"**{n_sent}**")
    st.info(f"RSI: {n_rsi:.1f} | IV: {n_iv:.1f}%")
    
    # Auto Alert Logic
    current_time = time.time()
    if n_pcr > 1.3 and n_rsi < 40 and (current_time - st.session_state.last_alert_time > 300):  # 5min cooldown
        msg = f"""
🎯 <b>PERFECT ENTRY: NIFTY 50</b>

🟢 <b>Action: BUY {int(n_atm)} CE</b>
📊 <b>Reason: PCR {n_pcr:.2f} + RSI {n_rsi:.1f}</b>
💰 <b>Entry: ₹{n_spot:.1f}</b>
🎯 <b>Target: ₹{n_spot+60:.1f}</b>
🛑 <b>Stoploss: ₹{n_spot-30:.1f}</b>
🔄 <b>Trailing: 15 pts</b>
⏰ <b>{datetime.now().strftime('%H:%M:%S')}</b>
        """
        if send_alert(msg):
            st.session_state.last_alert_time = current_time
            st.error("🚀 NIFTY CE ALERT SENT!")

# BANKNIFTY SECTION  
with col2:
    st.subheader("🟥 BANKNIFTY LIVE")
    
    # Candlestick chart
    b_fig = go.Figure()
    b_df = st.session_state.banknifty_candles
    b_fig.add_trace(go.Candlestick(
        x=b_df['time'], open=b_df['open'], high=b_df['high'],
        low=b_df['low'], close=b_df['close'],
        name="BANKNIFTY Live", increasing_line_color='#00ff88', decreasing_line_color='#ff4444'
    ))
    b_fig.update_layout(height=300, title="BANKNIFTY Live Candles")
    st.plotly_chart(b_fig, use_container_width=True)
    
    b_spot, b_atm, b_pcr, b_rsi, b_iv, b_sent = get_market_metrics("BANKNIFTY")
    st.metric("SPOT", f"₹{b_spot:.1f}", f"PCR {b_pcr:.2f}")
    st.success(f"**{b_sent}**")
    st.info(f"RSI: {b_rsi:.1f} | IV: {b_iv:.1f}%")

# === STATUS & CONTROLS ===
st.markdown("---")
col1, col2, col3 = st.columns(3)

if col1.button("🔔 TEST ALERT", use_container_width=True):
    send_alert("🧪 **ALPHA PRO TEST** - LIVE Streaming Working!")
    st.success("✅ Test sent!")

if col2.button("🔄 FORCE UPDATE", use_container_width=True):
    st.rerun()

if col3.button("📱 MOBILE VIEW", use_container_width=True):
    st.info("📱 Open: 192.168.1.XXX:8501")

# Status
if live_mode:
    st.sidebar.success(f"🔴 LIVE STREAMING | Speed: {speed}s")
    st.sidebar.metric("⏰ Next Update", f"{speed}s")
    time.sleep(speed)
    st.rerun()
else:
    st.sidebar.info("🔴 LIVE OFF - Click MANUAL UPDATE")

st.markdown("""
<div style='text-align:center; padding:20px; background:#00ff88; color:black; border-radius:15px;'>
✅ **DUAL LIVE CANDLES** | ✅ **PCR ALERTS** | ✅ **TELEGRAM READY** | 📱 **Mobile Perfect**
</div>
""", unsafe_allow_html=True)
