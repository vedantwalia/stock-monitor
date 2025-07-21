import yfinance as yf
import pandas as pd
import streamlit as st

@st.cache_data
def fetch_stock_data(ticker="RELIANCE.NS", period="7d", interval="1d"):
    """
    Fetch historical stock data for a given ticker symbol using period and interval.

    Parameters:
    ticker (str): The stock ticker symbol (e.g., 'RELIANCE.NS').
    period (str): The time range (e.g., '7d', '1mo', '1y').
    interval (str): The data interval (e.g., '1d', '1h', '15m').

    Returns:
    pandas.DataFrame: A DataFrame containing the stock data.
    """
    stock_data = yf.download(ticker, period=period, interval=interval)
    
    # Flatten multi-index if needed
    if isinstance(stock_data.columns, pd.MultiIndex):
        stock_data.columns = stock_data.columns.droplevel(1)
    stock_data["SMA_5"] = stock_data["Close"].rolling(window=5).mean()
    return stock_data