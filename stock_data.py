import yfinance as yf
import pandas as pd
import streamlit as st
import numpy as np

@st.cache_data
def compute_rsi(df, period=14):
    """
    Compute the Relative Strength Index (RSI) for a given DataFrame.
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing stock data with a 'Close' column.
    period (int): The number of periods to use for RSI calculation.
    
    Returns:
    pandas.Series: A Series containing the RSI values.
    """
    delta = df['Close'].diff()
    
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.ewm(span=period, min_periods=period).mean()
    avg_loss = loss.ewm(span=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(50)

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
    
    if not stock_data.empty and "Close" in stock_data.columns:
        stock_data["SMA_5"] = stock_data["Close"].rolling(window=5).mean()
        stock_data["SMA_10"] = stock_data["Close"].rolling(window=10).mean()
        stock_data["RSI_14"] = compute_rsi(stock_data)
        
    return stock_data