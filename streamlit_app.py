import streamlit as st
import plotly.express as px
import pandas as pd
from stock_data import fetch_stock_data
import requests
import yfinance as yf
from rapidfuzz import process, fuzz
import plotly.io as pio
import os
from dotenv import load_dotenv
from graph_utils import stock_chart

load_dotenv()
pio.templates.default = "plotly"  # Use full Plotly styling

if "API_KEY" in os.environ:
    API_KEY = os.getenv("API_KEY")
else:
    API_KEY = st.secrets["API_KEY"]

#------------------ Load NSE Tickers -----------------
@st.cache_data
def load_nse_ticker_map():
    df = pd.read_csv("nse_stocks_list.csv")
    df = df.dropna(subset=["SYMBOL", "NAME OF COMPANY"])
    ticker_map = {
        row["NAME OF COMPANY"].strip(): row["SYMBOL"].strip() + ".NS"
        for _, row in df.iterrows()
    }
    return ticker_map

TICKER_MAP = load_nse_ticker_map()

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

def find_best_match(query, choices, threshold=70):
    match = process.extractOne(query.upper(), choices, scorer=fuzz.WRatio)
    if match and match[1] >= threshold:
        return match[0]
    return None

matched_name = find_best_match(user_input, name_list)
if matched_name:
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
        elif not all(col in df.columns for col in ["Open", "High", "Low", "Close"]):
            st.error("❌ Required OHLC data is missing.")
            st.write(df.head())
        else:
            st.success("✅ Data loaded successfully")
            st.write(df.tail())

            # Create and display chart
            fig = stock_chart(df, ticker)
            st.plotly_chart(fig, use_container_width=True, render_mode="svg")

            # 📈 Live Price Display
            live_price = yf.Ticker(ticker).info.get("regularMarketPrice", "N/A")
            if isinstance(live_price, (float, int)):
                st.metric(label="📈 Live Price", value=f"₹ {live_price:,.2f}")
            else:
                st.metric(label="📈 Live Price", value="N/A")

# -------------- Market News Section --------------
st.subheader(":newspaper: Latest Market News")
news = fetch_market_news(API_KEY, query=user_input)

if news:
    for article in news[:10]:
        st.markdown(f"**[{article.get('title', '')}]({article.get('url', '#')})**")
        st.caption(article.get("publishedAt", ""))
        st.write(article.get("description", ""))
        st.markdown("---")
else:
    st.info("No news articles found.")