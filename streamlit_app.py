import streamlit as st
import plotly.express as px
import pandas as pd
from stock_data import fetch_stock_data
import requests
import yfinance as yf
from rapidfuzz import process

# ----------------- Constants -----------------
TICKER_MAP = {
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Larsen & Toubro": "LT.NS",
    "SBI": "SBIN.NS",
    "Axis Bank": "AXISBANK.NS",
    "Wipro": "WIPRO.NS",
    "ITC": "ITC.NS"
}

API_KEY = st.secrets["API_KEY"]

# ----------------- News Fetcher -----------------
@st.cache_data(show_spinner=False)
def fetch_market_news(api_key, query="NSE India"):
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("articles", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching news: {e}")
        return []

# ----------------- Streamlit UI -----------------
st.set_page_config(page_title="📈 Indian Stock Tracker", layout="centered")
st.title(":bar_chart: Indian Stock Tracker")

# -------------- User Input & Matching --------------
user_input = st.text_input("Enter stock name (e.g., Reliance)", "Reliance")
name_list = list(TICKER_MAP.keys())
matches = process.extract(user_input, name_list, limit=1, score_cutoff=60)

if matches:
    matched_name = matches[0][0]
    ticker = TICKER_MAP[matched_name]
    st.markdown(f"🔍 **Matched**: {matched_name} → **Ticker**: `{ticker}`")
else:
    st.warning("No matching stock found.")
    ticker = None

# -------------- Stock Options --------------
period = st.selectbox("Select period", ["1d", "5d", "7d", "1mo", "3mo", "6mo", "1y"])
interval = st.selectbox("Select interval", ["1m", "5m", "15m", "1h", "1d"])

# -------------- Fetch & Display Stock Data --------------
if st.button("Fetch") and ticker:
    with st.spinner("Fetching data..."):
        df = fetch_stock_data(ticker, period=period, interval=interval)

        if df.empty:
            st.error("❌ No data found.")
        else:
            st.success("✅ Data loaded successfully")
            st.write(df.tail())

            fig = px.line(df, x=df.index, y="Close", title=f"{ticker} Closing Prices")
            st.plotly_chart(fig, use_container_width=True)

            # Live Price
            live_price = yf.Ticker(ticker).info.get("regularMarketPrice", "N/A")
            st.metric(label="📈 Live Price", value=f"₹ {live_price}")

# -------------- Market News Section --------------
st.subheader(":newspaper: Latest Market News")
news = fetch_market_news(API_KEY, query=user_input)

if news:
    with st.container():
    st.markdown("""
        <div style='
            background-color: #1c1c1c;
            padding: 16px;
            border-radius: 8px;
            border: 1px solid #444;
            max-height: 300px;
            overflow-y: auto;
        '>
    """, unsafe_allow_html=True)

    for article in news[:10]:
        st.markdown(f"**[{article['title']}]({article['url']})**")
        st.caption(article["publishedAt"])
        st.write(article["description"])
        st.markdown("---")

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No news articles found.")
