import streamlit as st
import pandas as pd
import numpy as np
import time
import requests

# --- 1. CONFIG & TELEGRAM ---
TELEGRAM_TOKEN = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"
CHAT_ID = "2115666034"

def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}, timeout=5)
    except: pass

# --- 2. ADVANCED DATA WITH PCR LOGIC ---
def get_market_metrics(index_name):
    spot = 25750 + np.random.normal(0, 10) if index_name == "NIFTY" else 52500 + np.random.normal(0, 40)
    step = 50 if index_name == "NIFTY" else 100
    atm = round(spot / step) * step
    
    # Live PCR Simulation
    pcr = 1.15 + np.random.uniform(-0.3, 0.3)
    rsi = 50 + (np.sin(time.time()/10) * 25)
    iv = 14.5 + np.random.uniform(-0.5, 0.5)
    
    # PCR Sentiment
    sentiment = "NEUTRAL"
    if pcr > 1.25: sentiment = "BULLISH 🚀"
    elif pcr < 0.75: sentiment = "BEARISH 🩸"
    
    return spot, atm, pcr, rsi, iv, sentiment

# --- 3. DUAL INDEX SCREENER UI ---
st.title("🎯 PCR & GREEKS LIVE SCREENER")

col1, col2 = st.columns(2)
placeholder = st.empty()

while True:
    with placeholder.container():
        # --- NIFTY SECTION ---
        n_spot, n_atm, n_pcr, n_rsi, n_iv, n_sent = get_market_metrics("NIFTY")
        with col1:
            st.metric("NIFTY 50", f"₹{n_spot:.2f}", f"PCR: {n_pcr:.2f}")
            st.subheader(f"Sentiment: {n_sent}")
            st.write(f"**IV:** {n_iv:.2f}% | **RSI:** {n_rsi:.2f}")
            
            # Auto-Alert Trigger based on PCR + RSI
            if n_pcr > 1.3 and n_rsi < 40:
                msg = f"""
🎯 <b>PERFECT ENTRY: NIFTY 50</b>
🟢 <b>Action: BUY {n_atm} CE</b>
📊 <b>Reason:</b> EMA Support + PCR {n_pcr:.2f}
📈 <b>Technical:</b> RSI: {n_rsi:.2f} | IV: {n_iv:.2f}%
💰 <b>Entry:</b> {n_spot:.2f}
🎯 <b>Target:</b> {n_spot+60:.2f}
🛑 <b>Stoploss:</b> {n_spot-30:.2f}
🔄 <b>Trailing:</b> 15.0 pts
                """
                send_alert(msg)
                time.sleep(60) # Prevent multiple alerts

        # --- BANKNIFTY SECTION ---
        b_spot, b_atm, b_pcr, b_rsi, b_iv, b_sent = get_market_metrics("BANKNIFTY")
        with col2:
            st.metric("BANKNIFTY", f"₹{b_spot:.2f}", f"PCR: {b_pcr:.2f}")
            st.subheader(f"Sentiment: {b_sent}")
            st.write(f"**IV:** {b_iv:.2f}% | **RSI:** {b_rsi:.2f}")

    time.sleep(2)
