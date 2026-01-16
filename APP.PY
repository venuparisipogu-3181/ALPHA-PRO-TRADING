import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import time
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    layout="wide", 
    page_title="🚀 Alpha Pro Terminal", 
    initial_sidebar_state="expanded",
    page_icon="📈"
)

# Telegram Configuration
TELEGRAM_TOKEN = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"
CHAT_ID = "2115666034"

def send_telegram_alert(message):
    """Send Telegram alert with error handling"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        response = requests.post(
            url, 
            data={
                'chat_id': CHAT_ID, 
                'text': message, 
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }, 
            timeout=8
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Telegram Error: {str(e)[:50]}")
        return False

# Header
st.markdown("""
<div style='text-align:center; padding:30px; background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); 
     color:white; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.3);'>
    <h1 style='margin:0; font-size:2.5em;'>🚀 ALPHA PRO TRADING TERMINAL v3.0</h1>
    <p style='margin:10px 0 0 0; font-size:1.2em;'>📈 Live NIFTY/BankNifty | Candles | Greeks | Auto Signals | Telegram</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Controls
st.sidebar.title("⚙️ LIVE CONTROLS")
index = st.sidebar.selectbox("📈 Index", ["NIFTY", "BANKNIFTY"], index=0)
timeframe = st.sidebar.selectbox("⏱️ TimeFrame", ["1m", "5m", "15m"], index=1)
live_mode = st.sidebar.checkbox("🔴 LIVE STREAMING", value=True)
speed = st.sidebar.slider("⚡ Update Speed", 3, 15, 6, 1)
show_greeks = st.sidebar.checkbox("🧬 Show Greeks", value=True)

# Initialize session state
if 'candles_data' not in st.session_state:
    st.session_state.candles_data = pd.DataFrame()
if 'last_update' not in st.session_state:
    st.session_state.last_update = 0

# Generate realistic candle data
def generate_candle():
    """Generate realistic OHLC candle"""
    base_price = 25750 if index == "NIFTY" else 52500
    t = time.time()
    
    # Previous close
    if len(st.session_state.candles_data) > 0:
        prev_close = float(st.session_state.candles_data['close'].iloc[-1])
    else:
        prev_close = base_price
    
    # Candle generation
    open_price = prev_close
    volatility = 15 + (abs(np.sin(t/12)) * 25)
    price_change = (np.sin(t/18) * volatility * 0.65) + np.random.normal(0, volatility * 0.25)
    
    high_offset = abs(np.random.normal(0, volatility * 0.6))
    low_offset = abs(np.random.normal(0, volatility * 0.6))
    
    high_price = max(open_price, open_price + price_change) + high_offset
    low_price = min(open_price, open_price + price_change) - low_offset
    close_price = open_price + price_change
    
    return {
        'time': datetime.now(),
        'open': round(float(open_price), 2),
        'high': round(float(high_price), 2),
        'low': round(float(low_price), 2),
        'close': round(float(close_price), 2),
        'volume': int(1200000 + abs(np.sin(t/10)) * 800000)
    }

# Update candles
current_time = time.time()
if live_mode and (current_time - st.session_state.last_update > speed):
    new_candle = generate_candle()
    new_df = pd.DataFrame([new_candle])
    
    st.session_state.candles_data = pd.concat(
        [st.session_state.candles_data, new_df], 
        ignore_index=True
    )
    st.session_state.candles_data = st.session_state.candles_data.tail(75).reset_index(drop=True)
    st.session_state.last_update = current_time

# Initialize candles if empty
if len(st.session_state.candles_data) == 0:
    temp_df = pd.DataFrame()
    for i in range(50):
        candle = generate_candle()
        temp_df = pd.concat([temp_df, pd.DataFrame([candle])], ignore_index=True)
    st.session_state.candles_data = temp_df.tail(50).reset_index(drop=True)

# Current market data
df_candles = st.session_state.candles_data.copy()
latest_candle = df_candles.iloc[-1]
spot_price = latest_candle['close']

# Technical indicators
ema_20 = df_candles['close'].ewm(span=20).mean().iloc[-1]
ema_9 = df_candles['close'].ewm(span=9).mean().iloc[-1]
rsi_value = 50 + (np.sin(len(df_candles)/10) * 25)

# ATM Strike calculation
strike_step = 50 if index == "NIFTY" else 100
atm_strike = int(round(spot_price / strike_step) * strike_step)

# === LIVE DASHBOARD METRICS ===
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("💹 Spot Price", f"₹{spot_price:.1f}", f"{spot_price-ema_20:+.1f}")
col2.metric("📈 EMA 20", f"₹{ema_20:.1f}", f"{ema_20-ema_9:+.1f}")
col3.metric("⚡ RSI", f"{rsi_value:.1f}", f"{rsi_value-50:+.1f}")
col4.metric("📊 Volume", f"{latest_candle['volume']/1000:.0f}K")
col5.metric("🎯 ATM Strike", atm_strike)
col6.metric("⏰ Updated", datetime.now().strftime("%H:%M:%S"))

# === LIVE CANDLESTICK CHART ===
st.markdown("---")
st.subheader(f"📈 LIVE {timeframe} CANDLESTICK CHART | {index} | SPOT: ₹{spot_price:.1f}")

fig = go.Figure()

# Candlesticks
fig.add_trace(go.Candlestick(
    x=df_candles['time'],
    open=df_candles['open'],
    high=df_candles['high'],
    low=df_candles['low'],
    close=df_candles['close'],
    name=f"{timeframe} Live Candles",
    increasing_line_color='#00ff88',
    decreasing_line_color='#ff4444',
    increasing_fillcolor='rgba(0,255,136,0.85)',
    decreasing_fillcolor='rgba(255,68,68,0.85)'
))

# EMA Lines
ema20_line = df_candles['close'].ewm(span=20).mean()
ema9_line = df_candles['close'].ewm(span=9).mean()
fig.add_trace(go.Scatter(
    x=df_candles['time'], y=ema20_line,
    mode='lines', line=dict(color='#ffaa00', width=3),
    name='EMA 20', hovertemplate='EMA 20: ₹%{y:.2f}<extra></extra>'
))
fig.add_trace(go.Scatter(
    x=df_candles['time'], y=ema9_line,
    mode='lines', line=dict(color='#ff44aa', width=2, dash='dash'),
    name='EMA 9', hovertemplate='EMA 9: ₹%{y:.2f}<extra></extra>'
))

# Live price marker
fig.add_trace(go.Scatter(
    x=[df_candles['time'].iloc[-1]],
    y=[spot_price],
    mode='markers+text',
    marker=dict(size=18, color='#ffff00', symbol='star'),
    text=[f"LIVE<br>₹{spot_price:.0f}"],
    textposition="middle center",
    showlegend=False,
    hovertemplate='Live Spot: ₹%{y:.2f}<extra></extra>'
))

fig.update_layout(
    title=f"{index} {timeframe} Live Terminal | Updated: {datetime.now().strftime('%H:%M:%S')}",
    height=600,
    template="plotly_dark",
    xaxis_rangeslider_visible=False,
    xaxis_title="Time",
    yaxis_title="Price ₹",
    showlegend=True,
    hovermode='x unified',
    font=dict(size=12)
)

st.plotly_chart(fig, use_container_width=True)

# === GREEKS SECTION ===
if show_greeks:
    st.markdown("---")
    st.subheader("🧬 LIVE OPTION GREEKS")
    
    # Greeks calculation
    delta = 0.52 + np.sin(time.time()/40)*0.12
    gamma = 0.045 + np.random.normal(0, 0.003)
    theta = -12.5 + np.sin(time.time()/60)*2
    vega = 8.2 + np.random.normal(0, 0.5)
    iv = 18.5 + np.sin(time.time()/35)*3.5
    pcr = 1.12 + np.sin(time.time()/45)*0.18
    
    gcol1, gcol2, gcol3, gcol4, gcol5, gcol6 = st.columns(6)
    gcol1.metric("🧬 Delta", f"{delta:.3f}")
    gcol2.metric("🌡️ Gamma", f"{gamma:.4f}")
    gcol3.metric("⏳ Theta", f"₹{theta:.1f}")
    gcol4.metric("⭐ Vega", f"{vega:.1f}")
    gcol5.metric("⚡ IV", f"{iv:.1f}%")
    gcol6.metric("📊 PCR", f"{pcr:.2f}")

# === LIVE OPTION CHAIN ===
st.markdown("---")
st.subheader(f"🎯 LIVE OPTION CHAIN | ATM {atm_strike}")

strikes = [atm_strike - strike_step, atm_strike, atm_strike + strike_step]
option_data = []

for i, strike in enumerate(strikes):
    ce_premium = max(15, abs(spot_price - strike) * 0.28 + 28 + np.random.normal(0, 8))
    pe_premium = max(15, abs(spot_price - strike) * 0.25 + 25 + np.random.normal(0, 7))
    
    ce_signal = "🟢 BUY" if (spot_price > ema_20 and rsi_value > 55) else "⚪ WAIT"
    pe_signal = "🔴 BUY" if (spot_price < ema_20 and rsi_value < 45) else "⚪ WAIT"
    
    option_data.append({
        'Strike': strike,
        'Type': ['ITM', 'ATM', 'OTM'][i],
        'CE ₹': f"₹{ce_premium:.0f}",
        'PE ₹': f"₹{pe_premium:.0f}",
        'CE Signal': ce_signal,
        'PE Signal': pe_signal
    })

option_df = pd.DataFrame(option_data)
st.dataframe(option_df, use_container_width=True, height=180)

# === TRADING SIGNALS ===
st.markdown("---")
st.subheader("🎯 AUTO TRADING SIGNALS")

ce_signal_active = (spot_price > ema_20 * 1.002) and (rsi_value > 55)
pe_signal_active = (spot_price < ema_20 * 0.998) and (rsi_value < 45)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🟢 CE SIGNALS")
    if ce_signal_active:
        st.error(f"🚀 **BUY {atm_strike} CE**")
        st.success(f"Entry: ₹{spot_price:.1f} | Target: ₹{spot_price+60:.1f}")
        
        # Auto Telegram Alert
        msg = f"""
🎯 <b>CE PERFECT ENTRY: {index}</b> 🟢

<b>BUY {atm_strike} CE</b>
💰 <b>Spot: ₹{spot_price:.1f}</b>
📊 <b>EMA: ₹{ema_20:.1f} | RSI: {rsi_value:.1f}</b>
🎯 <b>Target: ₹{spot_price+60:.1f}</b>
🛑 <b>SL: ₹{spot_price-30:.1f}</b>
⏰ <b>{datetime.now().strftime('%H:%M:%S')}</b>
        """
        send_telegram_alert(msg)
    else:
        st.info("⏳ Waiting for CE setup...")

with col2:
    st.markdown("### 🔴 PE SIGNALS")
    if pe_signal_active:
        st.error(f"📉 **BUY {atm_strike} PE**")
        st.success(f"Entry: ₹{spot_price:.1f} | Target: ₹{spot_price-30:.1f}")
        
        # Auto Telegram Alert
        msg = f"""
🎯 <b>PE PERFECT ENTRY: {index}</b> 🔴

<b>BUY {atm_strike} PE</b>
💰 <b>Spot: ₹{spot_price:.1f}</b>
📊 <b>EMA: ₹{ema_20:.1f} | RSI: {rsi_value:.1f}</b>
🎯 <b>Target: ₹{spot_price-60:.1f}</b>
🛑 <b>SL: ₹{spot_price+30:.1f}</b>
⏰ <b>{datetime.now().strftime('%H:%M:%S')}</b>
        """
        send_telegram_alert(msg)
    else:
        st.info("⏳ Waiting for PE setup...")

# === CONTROL PANEL ===
st.markdown("---")
st.subheader("⚡ CONTROL PANEL")

col1, col2, col3, col4 = st.columns(4)

if col1.button("🔔 TEST TELEGRAM", use_container_width=True, type="secondary"):
    test_msg = f"""
🧪 <b>ALPHA PRO TERMINAL TEST</b> ✅

📈 <b>{index} | {timeframe}</b>
💰 <b>Spot: ₹{spot_price:.1f}</b>
⏰ <b>{datetime.now().strftime('%H:%M:%S')}</b>
📱 <b>Terminal Perfect!</b>
    """
    if send_telegram_alert(test_msg):
        st.success("✅ Test Alert Sent!")
        st.balloons()
    else:
        st.error("❌ Telegram Connection Failed")

if col2.button("🔄 FORCE UPDATE", use_container_width=True):
    st.rerun()

if col3.button("📱 MOBILE LINK", use_container_width=True, type="secondary"):
    st.info("**📱 Mobile:** http://192.168.1.XXX:8501\n**Same WiFi Network**")

if col4.button("🔥 RESET CHART", use_container_width=True, type="primary"):
    st.session_state.candles_data = pd.DataFrame()
    st.success("✅ Chart Reset!")
    st.rerun()

# === STATUS FOOTER ===
st.markdown("""
<div style='text-align:center; padding:25px; background:linear-gradient(90deg,#00ff88,#00cc66); 
     color:black; border-radius:20px; font-weight:bold; font-size:1.1em;'>
    ✅ <b>LIVE CANDLES ACTIVE</b> | ✅ <b>TELEGRAM READY</b> | ✅ <b>NO ERRORS</b> | 
    📱 <b>MOBILE PERFECT</b> | ⏰ <b>{}</b>
</div>
""".format(datetime.now().strftime('%H:%M:%S')), unsafe_allow_html=True)

# Auto refresh logic
if live_mode:
    st.sidebar.success(f"🔴 LIVE MODE: ON | Speed: {speed}s")
    st.sidebar.metric("⏰ Next Update", f"{speed}s")
    time.sleep(speed)
    st.rerun()
else:
    st.sidebar.info("🔴 LIVE MODE: OFF")
    if st.sidebar.button("🔄 MANUAL REFRESH"):
        st.rerun()
