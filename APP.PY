import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import time
import requests
from datetime import datetime

# --- 1. టెలిగ్రామ్ అలర్ట్ ఫంక్షన్ ---
def send_telegram_alert(message):
    # మీ ఒరిజినల్ వివరాలు ఇక్కడ పేస్ట్ చేయండి
    token = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"  
    chat_id = "2115666034"  
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id, 
        'text': message, 
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, data=payload, timeout=10)
        st.toast("✅ Telegram Alert Sent!")
    except Exception as e:
        st.error(f"Alert Failed: {str(e)}")

# --- 2. పేజీ సెటప్ ---
st.set_page_config(layout="wide", page_title="Alpha Pro Live Terminal")

# స్థిరమైన ప్లేస్‌హోల్డర్లు (స్క్రీన్‌షాట్‌లలోని డూప్లికేట్ ఎర్రర్స్ రాకుండా)
chart_placeholder = st.empty()
table_placeholder = st.empty()

# --- 3. సైడ్‌బార్ కంట్రోల్స్ ---
st.sidebar.title("⚙️ Strategy Control")
index_choice = st.sidebar.selectbox("📈 Index", ["NIFTY 50", "BANK NIFTY"], key="idx_unique")
tf_choice = st.sidebar.selectbox("⏱️ Timeframe", ["1m", "5m", "15m"], key="tf_unique")
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh (15s)", value=True)

symbol_map = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK"}

# --- 4. మెయిన్ లూప్ ---
while True:
    try:
        # డేటా డౌన్‌లోడ్ (RangeIndex Error ఫిక్స్)
        df = yf.download(symbol_map[index_choice], period="2d", interval=tf_choice, progress=False)
        if df.empty:
            continue
        
        df.reset_index(inplace=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # టైమ్ ఫార్మాట్ మరియు ఇండికేటర్లు
        df['time'] = pd.to_datetime(df.iloc[:, 0]).view('int64') // 10**9
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        last = df.iloc[-1]
        price = float(last['Close'])
        ema = float(last['EMA20'])
        rsi = float(last['RSI'])
        
        # సిగ్నల్ లాజిక్
        signal = "🚀 CE BUY" if (price > ema and rsi > 55) else "📉 PE BUY" if (price < ema and rsi < 45) else "😐 WAIT"
        current_ts = int(time.time())

        # === చార్ట్ మరియు గ్రీక్స్ ప్యానెల్ ===
        with chart_placeholder.container():
            g1, g2, g3, g4 = st.columns(4)
            g1.metric("💰 LTP", f"₹{price:.2f}", f"{price-ema:+.2f}")
            g2.metric("📈 EMA 20", f"₹{ema:.2f}")
            g3.metric("📊 RSI", f"{rsi:.1f}")
            g4.metric("💹 Signal", signal)
            
            st.markdown("---")
            
            # Candlestick Chart
            candles = df[['time', 'Open', 'High', 'Low', 'Close']].tail(60).rename(
                columns={'Open':'open','High':'high','Low':'low','Close':'close'}
            ).to_dict('records')
            
            # డూప్లికేట్ కీ రాకుండా టైమ్ స్టాంప్ వాడటం
            renderLightweightCharts([{
                "chart": {"layout": {"backgroundColor": "#0b0e11", "textColor": "#d1d4dc"}, "height": 350},
                "series": [{"type": 'Candlestick', "data": candles}]
            }], key=f"chart_{current_ts}")

        # === ఆప్షన్ స్ట్రైక్ టేబుల్ ===
        with table_placeholder.container():
            st.subheader("🎯 Perfect Strikes")
            step = 50 if "NIFTY" in index_choice else 100
            atm = int(round(price / step) * step)
            
            # Strikes selection
            if "CE" in signal:
                strikes = [atm - step, atm, atm + step]
                stype = "CE"
            else:
                strikes = [atm + step, atm, atm - step]
                stype = "PE"
            
            labels = ["ITM", "ATM", "OTM"]
            
            # టేబుల్ హెడర్స్
            h1, h2, h3, h4 = st.columns([1, 2, 2, 2])
            h1.write("**Type**")
            h2.write("**Strike**")
            h3.write("**LTP**")
            h4.write("**Action**")
            
            for i, s in enumerate(strikes):
                r1, r2, r3, r4 = st.columns([1, 2, 2, 2])
                r1.write(labels[i])
                r2.write(f"**{s} {stype}**")
                r3.write(f"₹{price:.2f}")
                
                # ప్రతి బటన్‌కు యూనిక్ కీ
                if r4.button(f"🚀 BUY {s}", key=f"btn_{s}_{current_ts}"):
                    msg = f"🎯 <b>ALPHA PRO ORDER</b>\nStrike: {s} {stype}\nType: {labels[i]}\nPrice: {price:.2f}"
                    send_telegram_alert(msg)
                    st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {e}")

    if auto_refresh:
        time.sleep(15)
        st.rerun()
    else:
        st.stop()
