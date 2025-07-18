import streamlit as st
import plotly.express as px
from stock_data import fetch_stock_data

st.title("📈 Indian Stock Tracker")

ticker = st.text_input("Enter NSE stock ticker (e.g., RELIANCE.NS)", "RELIANCE.NS")
period = st.selectbox("Select period", ["1d", "5d", "7d", "1mo", "3mo", "6mo", "1y"])
interval = st.selectbox("Select interval", ["1m", "5m", "15m", "1h", "1d"])

if st.button("Fetch"):
    with st.spinner("Fetching data..."):
        df = fetch_stock_data(ticker, period=period, interval=interval)

        if df.empty:
            st.error("❌ No data found.")
        else:
            st.write(df.tail())
            fig = px.line(df, x=df.index, y="Close", title=f"{ticker} Closing Prices")
            st.plotly_chart(fig, use_container_width=True)