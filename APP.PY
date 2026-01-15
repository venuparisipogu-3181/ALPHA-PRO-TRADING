import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import time
from datetime import datetime

# --- 1. పేజీ సెటప్ ---
st.set_page_config(layout="wide", page_title="Alpha Pro Trading")

# --- 2. టెలిగ్రామ్ అలర్ట్ ఫంక్షన్ (మీ టోకెన్స్ ఇక్కడ ఇవ్వండి) ---
def send_telegram_alert(message):
    token = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"  # BotFather నుండి
    chat_id = "2115666034"  # మీ గ్రూప్ ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception:
        pass

# UI ప్లేస్‌హోల్డర్లు (Sync Errors రాకుండా ఉండటానికి)
status_spot = st.empty()
chart_spot = st.empty()
table_spot = st.empty()

st.title("🚀 Alpha Pro - Live Trading Terminal")

# --- 3. మెయిన్ లూప్ ---
while True:
    try:
        # డేటా డౌన్‌లోడ్
        df = yf.download("^NSEI", period="2d", interval="1m", progress=False)
        
        if not df.empty:
            # Sync Error (RangeIndex) పరిష్కారం
            df.reset_index(inplace=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # ఇండికేటర్లు
            df['EMA20'] = ta.ema(df['Close'], length=20)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            last_row = df.iloc[-1]
            price = float(last_row['Close'])
            rsi_val = float(last_row['RSI'])
            ema_val = float(last_row['EMA20'])

            # 1. టాప్ మెట్రిక్స్ (Status Panel)
            with status_spot.container():
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("NIFTY 50", f"₹{price:.2f}")
                c2.metric("RSI (14)", f"{rsi_val:.1f}")
                c3.metric("EMA 20", f"₹{ema_val:.2f}")
                c4.write(f"⏰ Last Update: {datetime.now().strftime('%H:%M:%S')}")

            # 2. చార్ట్ డిస్ప్లే (Unique Key తో)
            with chart_spot:
                st.line_chart(df[['Close', 'EMA20']].tail(50))

            # 3. ఆప్షన్ టేబుల్ & సిగ్నల్ లాజిక్
            with table_spot.container():
                st.subheader("🎯 Live Signal & Option Chain")
                
                # సిగ్నల్ కండిషన్
                signal = "🚀 CE BUY" if price > ema_val and rsi_val > 55 else "📉 PE BUY" if price < ema_val and rsi_val < 45 else "😐 WAIT"
                st.info(f"Current Market Status: **{signal}**")

                atm = int(round(price / 50) * 50)
                strikes = [atm - 50, atm, atm + 50]
                labels = ["ITM", "ATM", "OTM"]

                # టేబుల్ కాలమ్స్
                cols = st.columns([1, 2, 2, 2])
                cols[0].write("**Type**")
                cols[1].write("**Strike**")
                cols[2].write("**Index LTP**")
                cols[3].write("**Action**")

                for i, s in enumerate(strikes):
                    r = st.columns([1, 2, 2, 2])
                    r[0].write(labels[i])
                    r[1].write(f"**{s} CE**")
                    r[2].write(f"₹{price:.2f}")
                    
                    # Duplicate Key Error పరిష్కారం: డైనమిక్ కీ వాడటం
                    if r[3].button(f"EXECUTE {s}", key=f"btn_{s}_{int(time.time())}"):
                        msg = f"🚀 <b>Alpha Pro Order</b>\nStrike: {s} CE\nPrice: ₹{price:.2f}\nTime: {datetime.now().strftime('%H:%M:%S')}"
                        send_telegram_alert(msg)
                        st.success(f"Sent alert for {s} CE!")
                        st.balloons()

    except Exception as e:
        st.error(f"Waiting for Data... {e}")
    
    # ఆటో రిఫ్రెష్
    time.sleep(15)
    st.rerun()
