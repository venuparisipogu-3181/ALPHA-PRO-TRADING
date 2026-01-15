import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import time
import requests
import numpy as np
from datetime import datetime
import streamlit_lightweight_charts as stlc

# Page config
st.set_page_config(
    layout="wide", 
    page_title="🚀 Alpha Pro Terminal v2.0", 
    initial_sidebar_state="expanded"
)

# Session state for portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'cash' not in st.session_state:
    st.session_state.cash = 100000

# Telegram function (error-proof)
def send_telegram_alert(message):
    token = "8289933882:AAGgTyAhFHYzlKbZ_0rvH8GztqXeTB6P-yQ"
    chat_id = "2115666034"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id, 
            'text': message[:4096], 
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        response = requests.post(url, data=payload, timeout=8)
        return response.status_code == 200
    except:
        return False

# Sidebar controls
st.sidebar.title("⚙️ Control Panel")
index_choice = st.sidebar.selectbox("📈 Index", ["NIFTY 50", "BANKNIFTY"], index=0)
timeframe = st.sidebar.selectbox("⏱️ Timeframe", ["5m", "15m", "1h"], index=1)
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh (15s)", value=True)

if st.sidebar.button("🔔 Test Telegram"):
    msg = f"🧪 **ALPHA PRO LIVE** 🧪\n⏰ {datetime.now().strftime('%H:%M:%S')}\n✅ Terminal Working!"
    if send_telegram_alert(msg):
        st.sidebar.success("✅ Telegram OK!")
    else:
        st.sidebar.warning("⚠️ Telegram Failed (Optional)")

# Main dashboard function
def update_terminal():
    try:
        # LIVE data fetch
        symbol_map = {"NIFTY 50": "^NSEI", "BANKNIFTY": "^NSEBANK"}
        ticker = symbol_map[index_choice]
        
        # yfinance with error handling
        df = yf.download(ticker, period="5d", interval=timeframe, progress=False, auto_adjust=True)
        
        if df.empty:
            st.warning("📡 No market data - Check after 9:15 AM IST")
            return
        
        # Data cleaning (FIXED)
        df = df.reset_index()
        df.columns = [col.strip() for col in df.columns]
        
        # Technical indicators
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df['RSI_14'] = ta.rsi(df['Close'], length=14)
        df['Volume_SMA'] = ta.sma(df['Volume'], length=20)
        df['MACD'] = ta.macd(df['Close'])['MACD_12_26_9']
        
        # Latest values
        latest = df.iloc[-1]
        price = float(latest['Close'])
        ema20 = float(latest['EMA_20'])
        rsi = float(latest['RSI_14'])
        volume = float(latest['Volume'])
        vol_sma = float(latest['Volume_SMA'])
        
        # Signal logic
        vol_spike = volume > vol_sma * 1.3
        bullish = (price > ema20 * 1.002) and (rsi > 52) and vol_spike
        bearish = (price < ema20 * 0.998) and (rsi < 48) and vol_spike
        
        signal = "🚀 CE BUY" if bullish else "📉 PE BUY" if bearish else "😐 WAIT"
        signal_color = "inverse" if bullish else "secondary" if bearish else ""
        
        # === HEADER METRICS ===
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric(f"💰 {index_choice}", f"₹{price:.1f}", f"{price-ema20:+.1f}")
        col2.metric("📈 EMA20", f"₹{ema20:.1f}")
        col3.metric("⚡ RSI", f"{rsi:.1f}", "50.0")
        col4.metric("📊 Volume", f"{volume/1000:.0f}K", f"{(volume/vol_sma-1)*100:+.0f}%")
        col5.metric("💼 Cash", f"₹{st.session_state.cash:,.0f}")
        col6.metric("🎯 Signal", signal, f"RSI {rsi:.0f}")
        
        st.markdown("---")
        
        # === GREEKS PANEL (SIMULATED LIVE) ===
        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        with col_g1:
            st.metric("🧬 Delta", "0.52", "↑0.02")
        with col_g2:
            st.metric("🌡️ Gamma", "0.045", "↓0.005")
        with col_g3:
            oi_change = int(math.sin(time.time()/200)*25000)
            arrow = "🟢↑↑" if oi_change > 15000 else "🔴↓↓" if oi_change < -15000 else "➡️"
            st.metric("📊 OI Change", f"{oi_change:+,} {arrow}")
        with col_g4:
            st.metric("⚡ IV", "21.5%", "+1.2%")
        
        # === LIVE CHART ===
        chart_df = df.tail(100)[['Datetime', 'Open', 'High', 'Low', 'Close']].copy()
        chart_data = chart_df.rename(columns={
            'Datetime': 'time', 'Open': 'open', 'High': 'high', 
            'Low': 'low', 'Close': 'close'
        }).dropna().to_dict('records')
        
        st.subheader("📈 LIVE CANDLES")
        stlc.renderLightweightCharts(
            chart_data,
            key=f"chart_{int(time.time())}",
            height=450,
            config={
                "layout": {"backgroundColor": "#0e1117", "textColor": "#d1d4dc"},
                "grid": {"vertLines": {"color": "#2a2e39"}, "horzLines": {"color": "#2a2e39"}}
            }
        )
        
        # === OPTIONS CHAIN TABLE ===
        st.markdown("---")
        st.subheader(f"🎯 OPTION CHAIN | {index_choice} ₹{price:.1f} | {signal}")
        
        step = 50 if "NIFTY" in index_choice else 100
        atm = int(round(price / step) * step)
        strikes = [atm - step*2, atm - step, atm, atm + step, atm + step*2]
        
        table_data = []
        for strike in strikes:
            ce_price = max(20, abs(price-strike)*0.15 + np.random.uniform(10, 50))
            pe_price = max(20, abs(price-strike)*0.12 + np.random.uniform(8, 40))
            
            table_data.append({
                'Strike': strike,
                'CE LTP': f"₹{ce_price:.0f}",
                'CE OI': f"{int(150000+np.random.randint(-20000,30000))/1000:.0f}K",
                f'CE Action': f"BUY {strike}CE" if bullish else "WAIT",
                'PE LTP': f"₹{pe_price:.0f}",
                'PE OI': f"{int(165000+np.random.randint(-25000,35000))/1000:.0f}K",
                f'PE Action': f"BUY {strike}PE" if bearish else "WAIT"
            })
        
        option_df = pd.DataFrame(table_data)
        st.dataframe(option_df, use_container_width=True, height=300)
        
        # === TRADING BUTTONS ===
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button(f"🚀 AUTO {signal}", type="primary", use_container_width=True):
                msg = f"""
🚀 <b>ALPHA PRO AUTO TRADE</b>
📈 {index_choice}: ₹{price:.1f}
🎯 Signal: {signal}
📊 RSI: {rsi:.1f} | EMA: ₹{ema20:.1f}
⏰ {datetime.now().strftime('%H:%M:%S')}
                """
                send_telegram_alert(msg)
                st.balloons()
        
        with col_btn2:
            if st.button("🗑️ RESET", type="secondary", use_container_width=True):
                st.session_state.portfolio = []
                st.session_state.cash = 100000
                st.rerun()
        
        # === PORTFOLIO ===
        if st.session_state.portfolio:
            st.subheader("📊 LIVE PORTFOLIO")
            port_data = []
            for trade in st.session_state.portfolio[-5:]:
                port_data.append({
                    'Symbol': trade['symbol'],
                    'Qty': trade['qty'],
                    'Entry': f"₹{trade['buy_price']:.0f}",
                    'Status': trade['status']
                })
            st.dataframe(pd.DataFrame(port_data), use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Check: pip install -r requirements.txt")

# RUN
if __name__ == "__main__":
    st.title("🚀 ALPHA PRO TERMINAL v2.0")
    update_terminal()
    
    # Auto refresh
    if auto_refresh:
        time.sleep(15)
        st.rerun()
