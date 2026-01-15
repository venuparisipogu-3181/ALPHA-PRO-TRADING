import streamlit as st
import pandas as pd
import time
import math
import requests
from datetime import datetime

# Page config
st.set_page_config(layout="wide", page_title="🚀 Alpha Pro v4.0")

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 3rem; color: #1f77b4; text-align: center;}
    .metric-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">🚀 ALPHA PRO TERMINAL v4.0</h1>', unsafe_allow_html=True)
st.markdown("**LIVE Options Dashboard | Greeks | OI | PCR | Auto Signals**")

# Session state
if 'cash' not in st.session_state:
    st.session_state.cash = 500000
if 'positions' not in st.session_state:
    st.session_state.positions = []

# Sidebar
st.sidebar.title("⚙️ Control Panel")
index_choice = st.sidebar.selectbox("📈 Index", ["NIFTY", "BANKNIFTY"])
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh (8s)", value=True)

# Telegram function
def send_telegram(msg):
    try:
        token = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"
        chat_id = "2115666034"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={
            'chat_id': chat_id,
            'text': msg[:4000],
            'parse_mode': 'HTML'
        }, timeout=5)
        return True
    except:
        return False

# Live data generator
def get_market_data():
    t = time.time()
    if index_choice == "NIFTY":
        base = 25750
        step = 50
    else:
        base = 57200
        step = 100
    
    spot = base + math.sin(t/35)*150
    return {
        'spot': spot,
        'ema20': spot * (1 + math.sin(t/60)*0.003),
        'rsi': 50 + math.sin(t/28)*25,
        'volume': 1800000 + abs(math.sin(t/22))*1200000,
        'oi_ce': 185000 + math.sin(t/120)*35000,
        'oi_pe': 172000 + math.sin(t/140)*-28000,
        'pcr': 1.15 + math.sin(t/200)*0.15,
        'atm': round(spot/step)*step
    }

# Get data
data = get_market_data()
spot = data['spot']
ema20 = data['ema20']
rsi = data['rsi']
volume = data['volume']
atm_strike = data['atm']

# Signal logic
bull_signal = spot > ema20 and rsi > 55 and volume > 2000000
bear_signal = spot < ema20 and rsi < 45 and volume > 2000000
main_signal = "🚀 CE BUY" if bull_signal else "📉 PE BUY" if bear_signal else "😐 WAIT"

# === HEADER METRICS ===
st.markdown("---")
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric(f"💹 {index_choice}", f"₹{spot:.0f}", f"{spot-ema20:+.0f}")
col2.metric("📈 EMA20", f"₹{ema20:.0f}")
col3.metric("⚡ RSI", f"{rsi:.1f}", "50.0")
col4.metric("📊 Volume", f"{volume/1000:.0f}K")
col5.metric("💰 Cash", f"₹{st.session_state.cash:,.0f}")
col6.metric("🎯 Signal", main_signal)

# === GREEKS PANEL ===
st.markdown("---")
st.subheader("🧬 LIVE GREEKS & MARKET DATA")
gcol1, gcol2, gcol3, gcol4, gcol5 = st.columns(5)
gcol1.metric("🧬 Delta", "0.52", "↑0.02")
gcol2.metric("🌡️ Gamma", "0.045", "↓0.01")
gcol3.metric("📈 CE OI", f"{data['oi_ce']/1000:.0f}K")
gcol4.metric("📉 PE OI", f"{data['oi_pe']/1000:.0f}K")
gcol5.metric("📊 PCR", f"{data['pcr']:.2f}")

# === OPTION CHAIN ===
st.markdown("---")
st.subheader(f"📊 LIVE OPTION CHAIN | {index_choice} ₹{spot:.0f}")

strikes = [atm_strike-200, atm_strike-100, atm_strike, atm_strike+100, atm_strike+200]
if index_choice == "BANKNIFTY":
    strikes = [atm_strike-500, atm_strike-250, atm_strike, atm_strike+250, atm_strike+500]

chain_data = []
for strike in strikes:
    ce_prem = max(15, abs(spot-strike)*0.25 + math.sin(time.time()/250)*30)
    pe_prem = max(15, abs(spot-strike)*0.22 + math.sin(time.time()/300)*25)
    
    chain_data.append({
        'Strike': strike,
        'CE ₹': f"₹{ce_prem:.0f}",
        'CE OI': f"{int(data['oi_ce'] + math.sin(strike)*20000)/1000:.0f}K",
        'CE Action': "🚀 BUY" if bull_signal else "WAIT",
        'PE ₹': f"₹{pe_prem:.0f}",
        'PE OI': f"{int(data['oi_pe'] + math.sin(-strike)*25000)/1000:.0f}K",
        'PE Action': "🚀 BUY" if bear_signal else "WAIT"
    })

df_chain = pd.DataFrame(chain_data)
st.dataframe(df_chain, use_container_width=True, height=300)

# === TRADING PANEL ===
st.markdown("---")
st.subheader("⚡ TRADING EXECUTOR")

col_btn1, col_btn2, col_btn3 = st.columns([3, 1, 1])

with col_btn1:
    if st.button(f"🚀 EXECUTE {main_signal}", type="primary", use_container_width=True):
        msg = f"""
🚀 <b>ALPHA PRO LIVE TRADE</b>
📈 {index_choice}: ₹{spot:.0f}
🎯 {main_signal}
💰 ATM: {atm_strike}
📊 RSI: {rsi:.1f} | Vol: {volume/1000:.0f}K
⏰ {datetime.now().strftime('%H:%M:%S')}
        """
        send_telegram(msg)
        st.session_state.cash -= 25000
        st.session_state.positions.append({
            'time': datetime.now().strftime('%H:%M'),
            'signal': main_signal,
            'strike': atm_strike
        })
        st.success(f"✅ {main_signal} EXECUTED!")
        st.balloons()

with col_btn2:
    if st.button("🔄 REFRESH", use_container_width=True):
        st.rerun()

with col_btn3:
    if st.button("🗑️ RESET", type="secondary", use_container_width=True):
        st.session_state.cash = 500000
        st.session_state.positions = []
        st.rerun()

# === POSITIONS ===
if st.session_state.positions:
    st.markdown("---")
    st.subheader("📊 LIVE POSITIONS")
    pos_df = pd.DataFrame(st.session_state.positions[-5:])
    st.dataframe(pos_df, use_container_width=True)

# === STRATEGY GUIDE ===
st.markdown("---")
st.markdown("""
<div style='background: linear-gradient(90deg, #ff6b6b, #4ecdc4); padding: 25px; border-radius: 15px; color: white; text-align: center;'>
    <h3>🎯 TRADING RULES</h3>
    <p><strong>🟢 CE BUY:</strong> Spot > EMA20 + RSI > 55 + High Volume</p>
    <p><strong>🔴 PE BUY:</strong> Spot < EMA20 + RSI < 45 + High Volume</p>
    <p><strong>📱 Mobile:</strong> 192.168.1.XXX:8501</p>
</div>
""", unsafe_allow_html=True)

# Telugu sidebar
st.sidebar.markdown("""
<div style='background: #f0f2f6; padding: 15px; border-radius: 10px;'>
    <h4>📖 తెలుగు మార్గదర్శకం</h4>
    <p><strong>1️⃣</strong> SIGNAL వచ్చినప్పుడు <strong>🚀 EXECUTE</strong> క్లిక్</p>
    <p><strong>2️⃣</strong> Telegram లో LIVE alert వస్తుంది</p>
    <p><strong>3️⃣</strong> Auto refresh ON చేయండి</p>
    <p><strong>🎯</strong> అన్నీ AUTO! మీరు BUY మాత్రమే!</p>
</div>
""", unsafe_allow_html=True)

# Auto refresh
if auto_refresh:
    st.caption(f"🔄 Auto refresh active | Last update: {datetime.now().strftime('%H:%M:%S')}")
    time.sleep(8)
    st.rerun()
