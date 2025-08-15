import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from pandas.tseries.offsets import BDay

# In your main Streamlit app, after fetching 
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
            
            # ADD THIS TRANSFORMATION BLOCK:
            # Handle MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
            
            # Ensure date is a column, not index
            if 'Date' not in df.columns and df.index.name in ['Date', 'Datetime'] or hasattr(df.index, 'date'):
                df = df.reset_index()
            
            # Standardize column names to lowercase
            df.columns = [col.lower() if isinstance(col, str) else col for col in df.columns]
            
            # Rename date column if needed
            if 'date' not in df.columns:
                for possible_date_col in ['Date', 'DATE', 'datetime', 'Datetime']:
                    if possible_date_col.lower() in df.columns:
                        df.rename(columns={possible_date_col.lower(): 'date'}, inplace=True)
                        break
            
            # Ensure date column exists
            if 'date' not in df.columns and len(df.columns) > 0:
                df.rename(columns={df.columns[0]: 'date'}, inplace=True)
            
            st.write(df.tail())

            # Create and display chart (this should now work)
            fig = stock_chart(df, ticker)
            st.plotly_chart(fig, use_container_width=True, render_mode="svg")
