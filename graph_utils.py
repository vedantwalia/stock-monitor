import plotly.graph_objects as go

def stock_chart(df, ticker):
    """
    Create a candlestick chart with volume for the given stock data
    
    Args:
        df (pd.DataFrame): DataFrame containing OHLCV data
        ticker (str): Stock ticker symbol
    
    Returns:
        go.Figure: Plotly figure object
    """
    fig = go.Figure()

    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price",
        increasing_line_color='green',
        decreasing_line_color='red'
    ))

    # Add volume if available
    if "Volume" in df.columns:
        fig.add_trace(go.Bar(
            x=df.index,
            y=df["Volume"],
            marker_color='rgba(128, 128, 128, 0.3)',
            yaxis='y2',
            name="Volume"
        ))
        fig.update_layout(
            yaxis2=dict(
                overlaying='y',
                side='right',
                showgrid=False,
                title='Volume'
            )
        )

    # Update layout
    fig.update_layout(
        title=f"{ticker} Candlestick Chart",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=600,
        margin=dict(l=10, r=10, t=50, b=10),
        template="plotly"
    )
    
    return fig