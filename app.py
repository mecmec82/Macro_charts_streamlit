import streamlit as st
import pandas as pd
import requests
import json
import numpy as np
import datetime

# --- CONFIGURATION ---
ALPHA_VANTAGE_API_KEY = st.secrets["alpha_vantage_api"]  # Store API key in Streamlit secrets

# --- FUNCTIONS ---
def get_daily_data(symbol, api_key):
    """Fetches daily adjusted data from Alpha Vantage."""
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        if 'Time Series (Daily)' in data:
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])
            return df
        elif 'Error Message' in data:
            st.error(f"Alpha Vantage API Error: {data['Error Message']}")
            return None
        else:
            st.error("Unexpected data format from Alpha Vantage API.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to Alpha Vantage API: {e}")
        return None

def calculate_sma(df, window):
    """Calculates Simple Moving Average."""
    return df['close'].rolling(window=window).mean()

def calculate_rsi(df, window):
    """Calculates Relative Strength Index."""
    delta = df['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_volatility(df, window):
    """Calculates simple historical volatility (standard deviation of daily returns)."""
    daily_returns = df['close'].pct_change().dropna()
    volatility = daily_returns.rolling(window=window).std() * np.sqrt(252) # Annualize volatility
    return volatility * 100 # Return in percentage

def classify_regime(df, short_sma_window=20, long_sma_window=200, rsi_window=14, vol_window=20):
    """Classifies market regime based on indicators."""
    short_sma = calculate_sma(df, short_sma_window)
    long_sma = calculate_sma(df, long_sma_window)
    rsi = calculate_rsi(df, rsi_window)
    volatility = calculate_volatility(df, vol_window)

    current_price = df['close'].iloc[-1]
    current_short_sma = short_sma.iloc[-1]
    current_long_sma = long_sma.iloc[-1]
    current_rsi = rsi.iloc[-1]
    current_volatility = volatility.iloc[-1]

    if current_price > current_long_sma and current_short_sma > current_long_sma and current_rsi < 70 and current_volatility < 25: # Example thresholds, adjust as needed
        regime = "Bull Market"
    elif current_price < current_long_sma and current_short_sma < current_long_sma and current_rsi > 30 and current_volatility > 20: # Example thresholds, adjust as needed
        regime = "Bear Market"
    else:
        regime = "Sideways/Neutral Market" # Or "Uncertain", etc.

    return regime, current_price, current_short_sma, current_long_sma, current_rsi, current_volatility, short_sma, long_sma, rsi, volatility

# --- STREAMLIT APP ---
st.title("Stock Market Regime Dashboard")

st.markdown("""
This dashboard provides an *indication* of the current stock market regime based on simple technical indicators using non-premium Alpha Vantage API data.
**It's for informational purposes only and not financial advice.**  Market regimes are complex and this is a simplified model.

**Indicators Used:**
* **20-day and 200-day Simple Moving Averages (SMA):** To identify trend direction.
* **14-day Relative Strength Index (RSI):** To gauge momentum and overbought/oversold conditions.
* **20-day Historical Volatility:**  Estimated from daily price changes to assess market volatility.

**Regime Definitions (Simplified):**
* **Bull Market:** Generally characterized by rising prices, positive sentiment, and often lower volatility.
* **Bear Market:** Generally characterized by falling prices, negative sentiment, and often higher volatility.
* **Sideways/Neutral Market:**  Lack of a clear trend, price consolidation, and moderate volatility.
""")

stock_symbol = st.sidebar.selectbox("Select Stock Ticker (Broad Market ETF recommended):", ['SPY', 'QQQ', 'DIA', 'IWM'])  # Add more if needed
if not ALPHA_VANTAGE_API_KEY:
    st.sidebar.warning("Please enter your Alpha Vantage API key in Streamlit secrets.")
else:
    if stock_symbol:
        st.header(f"Regime Analysis for: {stock_symbol}")
        data_df = get_daily_data(stock_symbol, ALPHA_VANTAGE_API_KEY)

        if data_df is not None:
            # Rename columns for easier access
            data_df.rename(columns={'4. close': 'close'}, inplace=True)

            regime, current_price, current_short_sma, current_long_sma, current_rsi, current_volatility, short_sma, long_sma, rsi, volatility = classify_regime(data_df)

            st.subheader("Current Market Regime Indication:")
            st.markdown(f"<h2 style='text-align: center; color: {'green' if regime == 'Bull Market' else ('red' if regime == 'Bear Market' else 'orange')};'>{regime}</h2>", unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Current Price", f"${current_price:.2f}")
            col2.metric("20-day SMA", f"${current_short_sma:.2f}")
            col3.metric("200-day SMA", f"${current_long_sma:.2f}")

            col4, col5 = st.columns(2)
            col4.metric("14-day RSI", f"{current_rsi:.2f}")
            col5.metric("20-day Volatility (Annualized)", f"{current_volatility:.2f}%")

            st.subheader("Price Chart with Moving Averages")
            chart_data = pd.DataFrame({
                'Price': data_df['close'],
                '20-day SMA': short_sma,
                '200-day SMA': long_sma
            }).dropna()
            st.line_chart(chart_data)

            st.subheader("RSI")
            rsi_data = pd.DataFrame({'RSI': rsi}).dropna()
            st.line_chart(rsi_data)

            st.subheader("Volatility (Annualized)")
            volatility_data = pd.DataFrame({'Volatility': volatility}).dropna()
            st.line_chart(volatility_data)

            st.info("**Disclaimer:** This dashboard provides a simplified indication of market regimes based on common technical indicators.  Market conditions are constantly evolving, and this analysis should not be considered definitive financial advice. Always conduct your own thorough research and consult with a financial professional before making investment decisions.")

    else:
        st.info("Select a stock ticker symbol from the sidebar to begin analysis.")
