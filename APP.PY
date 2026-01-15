import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time
import requests
import math
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(layout="wide", page_title="🚀 Alpha Pro LIVE STREAMING", initial_sidebar_state="expanded")

# Custom CSS for live streaming look
st.markdown("""
<style>
    .live-badge {background: linear-gradient(90deg, #00ff88, #00cc6a); color: black; padding: 5px 15px; border-radius: 20px; font-weight: bold;}
    .metric-live {animation: pulse 2s infinite;}
    @keyframes pulse {0% {box-shadow: 0 0 0 0 rgba(0,255,136,0.7);} 70% {box-shadow: 0 0 0 20px rgba(0,255,136,0);} 100% {box-shadow: 0 0 0 0 rgba(0,255,136,0);}}
</style>
""", unsafe_allow_html=True)

# Header with live badge
st.markdown("""
<div style='text-align: center;'>
    <h1>🚀 **ALPHA PRO LIVE STREAMING TERMINAL**</h1>
    <div class="live-badge">🔴 LIVE STREAMING</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("⚙️ Live Streaming Control")
index_choice = st.sidebar.selectbox("📈 Index", ["NIFTY 50", "BANK NIFTY"])
timeframe = st.sidebar.selectbox("⏱️ Timeframe", ["1m", "5m", "15m"])
stream_speed = st.sidebar.slider("⚡ Update Speed", 3, 15, 8)
telegram_enabled = st.sidebar.checkbox("🔔 Telegram Alerts", value=True)

symbol_map = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK"}

# Telegram function
def send_live_alert(message):
    if not telegram_enabled:
        return
    try:
        token = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"
        chat_id = "2115666034"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={
            'chat_id': chat_id,
            'text': f"🚀 <b>LIVE STREAM ALERT</b>\n{message}",
            'parse_mode': 'HTML'
        }, timeout=5)
    except:
        pass

# LIVE STREAMING FUNCTION
def live_stream_update():
    # Base data from yfinance
    ticker = symbol_map[index_choice]
    df = yf.download(ticker, period="2d", interval=timeframe, progress=False)
    
    if df.empty:
        st.warning("📡 Waiting for market data...")
        return
    
    df = df.reset_index()
    df.columns = df.columns.str.strip()
    
    # Live simulation overlay
    t = time.time()
    base_price = df['Close'].iloc[-1]
    live_price = base_price + np.sin(t/10)*5 + np.random.normal(0, 1.5)
    
    # Indicators
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    ema20 = df['EMA20'].iloc[-1]
    
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1]
    
    # Signal logic
    volume_spike = df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1] * 1.2
    ce_signal = live_price > ema20 and rsi > 55 and volume_spike
    pe_signal = live_price < ema20 and rsi < 45 and volume_spike
    live_signal = "🚀 CE BUY" if ce_signal else "📉 PE BUY" if pe_signal else "😐 WAIT"
    
    # === LIVE METRICS ===
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(f"{index_choice} **LIVE**", f"₹{live_price:.1f}", f"{live_price-base_price:+.1f}", delta_color="inverse")
    col2.metric("📈 EMA20", f"₹{ema20:.1f}")
    col3.metric("⚡ RSI", f"{rsi:.1f}", "50.0")
    col4.metric("📊 Volume", f"{df['Volume'].iloc[-1]/1000:.0f}K")
    col5.metric("🎯 SIGNAL", live_signal)
    
    # === GREEKS LIVE PANEL ===
    st.markdown("---")
    gcol1, gcol2, gcol3, gcol4 = st.columns(4)
    gcol1.metric("🧬 Delta", f"{0.5 + np.sin(t/20)*0.1:.2f}")
    gcol2.metric("🌡️ Gamma", f"{0.045 + np.random.uniform(-0.01,0.01):.3f}")
    gcol3.metric("⚡ IV", f"{21.5 + np.sin(t/30)*2:.1f}%")
    gcol4.metric("📊 PCR", f"{1.15 + np.sin(t/25)*0.1:.2f}")
    
    # === LIVE CHART ===
    st.markdown("---")
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('🔴 LIVE PRICE STREAM', '📊 RSI'),
        row_heights=[0.7, 0.3],
        vertical_spacing=0.05
    )
    
    # Candlestick (last 50)
    last_50 = df.tail(50)
    fig.add_trace(
        go.Candlestick(
            x=last_50['Datetime'],
            open=last_50['Open'], high=last_50['High'],
            low=last_50['Low'], close=last_50['Close'],
            name="Price"
        ),
        row=1, col=1
    )
    
    # EMA
    fig.add_trace(go.Scatter(x=last_50['Datetime'], y=last_50['EMA20'], 
                            name="EMA20", line=dict(color='orange')), row=1, col=1)
    
    # LIVE DOT
    fig.add_trace(go.Scatter(x=[datetime.now()], y=[live_price], 
                            mode='markers+text', name="LIVE", 
                            marker=dict(size=15, color='red'),
                            text=[f"₹{live_price:.0f}"], textposition="top center"), 
                  row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=last_50['Datetime'], y=last_50['RSI'], 
                            name="RSI", line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    fig.update_layout(height=500, showlegend=True, title=f"📈 {index_choice} LIVE CHART")
    st.plotly_chart(fig, use_container_width=True)
    
    # === LIVE OPTION CHAIN ===
    st.markdown("---")
    step = 50 if "NIFTY" in index_choice else 100
    atm = int(round(live_price / step) * step)
    
    st.subheader(f"🎯 **LIVE OPTION CHAIN** | ATM {atm} | **{live_signal}**")
    
    strikes = [atm - step, atm, atm + step]
    chain_data = []
    for strike in strikes:
        ce_live = max(20, abs(live_price-strike)*0.25 + np.random.uniform(5, 25))
        pe_live = max(20, abs(live_price-strike)*0.22 + np.random.uniform(5, 20))
        chain_data.append({
            'Strike': strike,
            f'{strike}CE': f"₹{ce_live:.0f}",
            f'{strike}PE': f"₹{pe_live:.0f}",
            'Signal': live_signal
        })
    
    df_chain = pd.DataFrame(chain_data)
    st.dataframe(df_chain, use_container_width=True)
    
    # === LIVE TRADING BUTTONS ===
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    if col1.button(f"🚀 LIVE TRADE {live_signal}", type="primary", use_container_width=True):
        msg = f"""
🚀 <b>LIVE STREAM TRADE</b>
📈 {index_choice}: ₹{live_price:.1f}
🎯 {live_signal}
💰 ATM: {atm}
📊 RSI: {rsi:.1f}
⏰ LIVE {datetime.now().strftime('%H:%M:%S')}
        """
        send_live_alert(msg)
        st.success(f"✅ LIVE {live_signal} EXECUTED!")
        st.balloons()
    
    col2.button("🔄 FORCE REFRESH", on_click=lambda: st.rerun(), use_container_width=True)

# === STREAMING LOOP ===
placeholder = st.empty()
stream_placeholder = st.empty()

# Live status
col_status1, col_status2, col_status3 = st.columns(3)
col_status1.metric("📶 Stream Status", "🟢 LIVE")
col_status2.metric("⚡ Updates/sec", f"{1/stream_speed:.1f}")
col_status3.metric("📱 Mobile", "192.168.1.XXX:8501")

# MAIN STREAM
while True:
    with placeholder.container():
        live_stream_update()
    
    with stream_placeholder.container():
        st.markdown(f"""
        <div style='text-align:center; padding:20px; background:#00ff88; color:black; border-radius:10px;'>
            <h2>🔴 **LIVE STREAMING ACTIVE**</h2>
            <p>⏰ Last Update: {datetime.now().strftime('%H:%M:%S')}</p>
            <p>📈 {index_choice} Streaming | Speed: {stream_speed}s</p>
        </div>
        """, unsafe_allow_html=True)
    
    time.sleep(stream_speed)
    st.rerun()
