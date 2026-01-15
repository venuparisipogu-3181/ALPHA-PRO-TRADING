import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import time
import requests
from datetime import datetime

# --- 1. TELEGRAM అలర్ట్ ఫంక్షన్ ---
def send_telegram_alert(message):
    token = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"
    chat_id = "2115666034"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=payload, timeout=10)
        return True
    except Exception as e:
        st.error(f"Alert Failed: {str(e)}")
        return False

# --- 2. పేజీ సెటప్ ---
st.set_page_config(layout="wide", page_title="🚀 Alpha Pro Live Terminal")

# స్థిరంగా ఉండే ప్లేస్‌హోల్డర్లు
header_area = st.empty()
chart_area = st.empty()
table_area = st.empty()
status_area = st.empty()

# --- 3. సైడ్‌బార్ ---
st.sidebar.title("⚙️ Strategy Control")
index_choice = st.sidebar.selectbox("📈 Index", ["NIFTY 50", "BANK NIFTY"], key="idx_unique")
tf_choice = st.sidebar.selectbox("⏱️ Timeframe", ["1m", "5m", "15m"], key="tf_unique")
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh (15s)", value=True)

symbol_map = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK"}

# --- 4. డేటా & లాజిక్ ఫంక్షన్ ---
def run_terminal():
    curr_ts = str(int(time.time()))
    try:
        # Data fetch
        df = yf.download(symbol_map[index_choice], period="2d", interval=tf_choice, progress=False)
        if df.empty: return

        df.reset_index(inplace=True)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df['time'] = pd.to_datetime(df.iloc[:, 0]).view('int64') // 10**9
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['Volume_MA'] = ta.sma(df['Volume'], length=20)
        
        last = df.iloc[-1]
        price, ema, rsi, vol, vol_ma = float(last['Close']), float(last['EMA20']), float(last['RSI']), float(last['Volume']), float(last['Volume_MA'])
        
        # Signal Logic
        vol_cond = vol > (vol_ma * 1.2) # 1.2x volume for better signals
        signal = "🚀 CE BUY" if (price > ema and rsi > 55 and vol_cond) else "📉 PE BUY" if (price < ema and rsi < 45 and vol_cond) else "😐 WAIT"

        # === GREEKS & CHART ===
        with chart_area.container():
            g1, g2, g3, g4, g5, g6 = st.columns(6)
            g1.metric("🧬 Delta", "0.52")
            g2.metric("🌡️ Gamma", "0.08")
            g3.metric("📊 OI Change", "+15K")
            g4.metric("⚡ IV", "18.5%")
            g5.metric("📉 PCR", "1.12")
            g6.metric("💹 Signal", signal, delta=f"RSI: {rsi:.1f}")
            
            candles = df[['time', 'Open', 'High', 'Low', 'Close']].tail(50).rename(columns={'Open':'open','High':'high','Low':'low','Close':'close'}).to_dict('records')
            renderLightweightCharts([{"chart": {"layout": {"backgroundColor": "#0b0e11", "textColor": "#d1d4dc"}, "height": 350}, "series": [{"type": 'Candlestick', "data": candles}]}], key=f"c_{curr_ts}")

        # === OPTION CHAIN TABLE (Manual Action Buttons) ===
        with table_area.container():
            st.markdown(f"### 📊 Option Chain Screener | {index_choice} **₹{price:.2f}**")
            if signal != "😐 WAIT":
                step = 50 if "NIFTY 50" in index_choice else 100
                atm = int(round(price / step) * step)
                strikes = [atm - step, atm, atm + step] if "CE" in signal else [atm + step, atm, atm - step]
                types = ["ITM", "ATM", "OTM"]
                sig_type = signal.split()[1]

                cols = st.columns([1, 2, 2, 2])
                cols[0].write("**Type**"); cols[1].write("**Strike**"); cols[2].write("**LTP**"); cols[3].write("**Action**")
                
                for i, s in enumerate(strikes):
                    r = st.columns([1, 2, 2, 2])
                    r[0].write(types[i])
                    r[1].write(f"**{s} {sig_type}**")
                    r[2].write(f"₹{price:.2f}")
                    if r[3].button(f"🚀 BUY {s}", key=f"btn_{s}_{curr_ts}"):
                        msg = f"🚀 <b>ALPHA PRO ORDER</b>\nIndex: {index_choice}\nStrike: {s} {sig_type}\nLTP: ₹{price:.2f}\nSignal: {signal}"
                        send_telegram_alert(msg)
                        st.balloons()
            else:
                st.info("⏳ Waiting for Price > EMA20 and RSI > 55 Conditions...")

    except Exception as e:
        st.error(f"Error: {e}")

# --- 5. EXECUTION ---
if __name__ == "__main__":
    run_terminal()
    if auto_refresh:
        time.sleep(15)
        st.rerun()
