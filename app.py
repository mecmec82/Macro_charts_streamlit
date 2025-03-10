import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta

# --- Configuration ---
DEFAULT_SYMBOL = "^GSPC"  # Default S&P 500 Index symbol
DEFAULT_VIX_SYMBOL = "^VIX"  # Default VIX symbol (Note: VIX data might be harder to get for free from Alpha Vantage. May need proxy or alternative source)
MA_SHORT_PERIOD = 50
MA_LONG_PERIOD = 200
VIX_THRESHOLD_HIGH = 25
VIX_THRESHOLD_LOW = 20
LOOKBACK_DAYS = 730  # ~2 years of data for MAs and trend analysis

# --- Data Fetching Functions (using Alpha Vantage FREE endpoints) ---
def fetch_stock_data_alphavantage_free(symbol, api_key, period="max"):
    """Fetches historical stock data from Alpha Vantage FREE TIME_SERIES_DAILY endpoint (unadjusted)."""
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={api_key}" # Using TIME_SERIES_DAILY (FREE)

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if 'Time Series (Daily)' in data: # Using 'Time Series (Daily)' key for FREE endpoint
            time_series_data = data['Time Series (Daily)']
            df = pd.DataFrame.from_dict(time_series_data, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            # Rename columns to standard names (like yfinance) - using unadjusted data column names
            df.rename(columns={
                '1. open': 'Open',
                '2. high': 'High',
                '3. low': 'Low',
                '4. close': 'Close',
                '5. volume': 'Volume' # No 'Adj Close' in TIME_SERIES_DAILY (unadjusted)
            }, inplace=True)
            return df
        elif 'Error Message' in data:
            st.error(f"Alpha Vantage API Error for {symbol}: {data['Error Message']}")
            return None
        else:
            st.error(f"Unknown error fetching data for {symbol} from Alpha Vantage. Response: {data}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Request error to Alpha Vantage: {e}")
        return None
    except json.JSONDecodeError:
        st.error("Error decoding JSON response from Alpha Vantage.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None


def fetch_vix_data_alphavantage_free(symbol, api_key, period="max"):
    """Fetches historical VIX data (using proxy symbol if needed) from Alpha Vantage FREE endpoints.
       Note: VIX itself (^VIX) might not be directly available for free. You might need to use a proxy ETF (like VXX)
       or find another FREE API source for VIX data.  For now, we'll attempt to fetch data for the given VIX symbol
       using the FREE TIME_SERIES_DAILY endpoint. If it fails, consider using a VIX proxy ETF symbol or alternative API."""
    return fetch_stock_data_alphavantage_free(symbol, api_key, period) # Reusing stock data function for VIX for now


# --- Indicator Calculation Functions (same as before) ---
def calculate_moving_averages(data, short_period, long_period):
    """Calculates short and long term moving averages."""
    if data is None or data.empty:
        return None, None
    ma_short = data['Close'].rolling(window=short_period).mean()
    ma_long = data['Close'].rolling(window=long_period).mean()
    return ma_short, ma_long

def get_trend_direction_ma(data, ma_short, ma_long):
    """Determines trend direction based on moving average crossover and position."""
    if data is None or ma_short is None or ma_long is None:
        return "Neutral (Data Missing)"

    last_close = data['Close'].iloc[-1]
    ma_short_current = ma_short.iloc[-1]
    ma_long_current = ma_long.iloc[-1]
    ma_short_prev = ma_short.iloc[-2] if len(ma_short) > 1 else ma_short_current #Handle edge case first day
    ma_long_prev = ma_long.iloc[-2] if len(ma_long) > 1 else ma_long_current #Handle edge case first day


    if ma_short_current > ma_long_current and ma_short_prev <= ma_long_prev:
        return "Potential Uptrend (Golden Cross)" #Golden Cross
    elif ma_short_current < ma_long_current and ma_short_prev >= ma_long_prev:
        return "Potential Downtrend (Death Cross)" #Death Cross
    elif last_close > ma_short_current and last_close > ma_long_current and ma_short_current > ma_long_current:
        return "Uptrend (Above MAs)"
    elif last_close < ma_short_current and last_close < ma_long_current and ma_short_current < ma_long_current:
        return "Downtrend (Below MAs)"
    else:
        return "Neutral (Between MAs or Mixed)"

def get_vix_regime(vix_data, high_threshold, low_threshold):
    """Determines market regime based on VIX level."""
    if vix_data is None or vix_data.empty:
        return "Neutral (VIX Data Missing)"

    current_vix = vix_data['Close'].iloc[-1]

    if current_vix > high_threshold:
        return "Bearish (High Volatility)"
    elif current_vix < low_threshold:
        return "Bullish (Low Volatility)"
    else:
        return "Neutral (Moderate Volatility)"


# --- Overall Regime Indicator Function (same as before) ---
def determine_overall_regime(trend_direction, vix_regime):
    """Combines indicators to determine overall market regime."""

    if "Downtrend" in trend_direction or "Bearish" in vix_regime:
        if "Uptrend" in trend_direction or "Bullish" in vix_regime: #mixed signals
            return "Uncertain/Mixed"
        else:
            return "Downtrend Regime"
    elif "Uptrend" in trend_direction or "Bullish" in vix_regime:
        return "Uptrend Regime"
    else:
        return "Neutral Regime"


# --- Streamlit App ---
def main():
    st.title("Market Regime Indicator (Alpha Vantage - FREE API)")
    st.markdown("Using Alpha Vantage **FREE API** endpoints (TIME_SERIES_DAILY). Data is **unadjusted** for dividends/splits. Limited historical data may be available depending on the symbol and API free tier limits.")
    st.markdown("For VIX data, free API access might be limited. Consider using a VIX proxy ETF symbol (like VXX) or an alternative free VIX data source if needed.")
    st.markdown("API call frequency limits apply to the free tier. Please be mindful of usage.")
    st.markdown("---")

    st.sidebar.header("Settings")
    alpha_vantage_api_key = st.sidebar.text_input("Alpha Vantage API Key", type="password")
    symbol = st.sidebar.text_input("Stock Index Symbol (e.g., ^GSPC or SPY)", DEFAULT_SYMBOL)
    vix_symbol = st.sidebar.text_input("VIX Symbol (e.g., ^VIX or VXX - VIX data source may be limited in free API)", DEFAULT_VIX_SYMBOL)
    ma_short_period_input = st.sidebar.number_input("Short MA Period", min_value=1, value=MA_SHORT_PERIOD)
    ma_long_period_input = st.sidebar.number_input("Long MA Period", min_value=1, value=MA_LONG_PERIOD)
    vix_high_threshold_input = st.sidebar.number_input("VIX High Threshold", value=VIX_THRESHOLD_HIGH)
    vix_low_threshold_input = st.sidebar.number_input("VIX Low Threshold", value=VIX_THRESHOLD_LOW)

    if st.sidebar.button("Analyze"):
        if not alpha_vantage_api_key:
            st.sidebar.error("Please enter your Alpha Vantage API Key.")
            st.stop()

        with st.spinner("Fetching and analyzing data from Alpha Vantage FREE API..."):
            end_date = datetime.today()
            start_date = end_date - timedelta(days=LOOKBACK_DAYS)
            period_str = f"{start_date.strftime('%Y-%m-%d')}:{end_date.strftime('%Y-%m-%d')}"

            stock_data = fetch_stock_data_alphavantage_free(symbol, alpha_vantage_api_key, period=period_str)
            vix_data = fetch_vix_data_alphavantage_free(vix_symbol, alpha_vantage_api_key, period=period_str)

            if stock_data is not None:
                ma_short, ma_long = calculate_moving_averages(stock_data, ma_short_period_input, ma_long_period_input)
                trend_direction_ma = get_trend_direction_ma(stock_data, ma_short, ma_long)
            else:
                trend_direction_ma = "Neutral (Stock Data Error)"

            vix_regime = get_vix_regime(vix_data, vix_high_threshold_input, vix_low_threshold_input)

            overall_regime = determine_overall_regime(trend_direction_ma, vix_regime)

            st.header("Market Regime Indicators")
            st.subheader(f"Symbol: {symbol}")

            col1, col2 = st.columns(2)
            col1.metric(f"MA Trend ({ma_short_period_input} vs {ma_long_period_input} day)", trend_direction_ma)
            col2.metric(f"VIX Regime (Thresholds: High>{vix_high_threshold_input}, Low<{vix_low_threshold_input})", vix_regime)

            st.subheader("Overall Market Regime")
            st.markdown(f"<h2 style='text-align: center; color: blue;'>{overall_regime}</h2>", unsafe_allow_html=True) # Make overall regime prominent

            if stock_data is not None:
                chart_data = stock_data[['Close']].copy()
                if ma_short is not None:
                    chart_data['MA_Short'] = ma_short
                if ma_long is not None:
                    chart_data['MA_Long'] = ma_long
                st.subheader(f"{symbol} Price with Moving Averages (Unadjusted)") # Indicate unadjusted data
                st.line_chart(chart_data)

            if vix_data is not None:
                st.subheader(f"{vix_symbol} (VIX) Chart (Data source may be limited in FREE API)") # Add disclaimer about VIX data source
                st.line_chart(vix_data[['Close']])


            st.markdown("---")
            st.subheader("Interpretation & Disclaimer (FREE API Limitations)")
            st.write("* This is a simplified market regime indicator for educational purposes only and not financial advice.")
            st.write("* It uses Moving Averages and VIX as indicators. Real market analysis requires more comprehensive data and tools.")
            st.write("* Data is from Alpha Vantage **FREE API**, using **unadjusted** daily price data (TIME_SERIES_DAILY).")
            st.write("* **Data is unadjusted for dividends and stock splits.** For long-term analysis or precise returns, adjusted data is preferred but might require a paid API subscription.")
            st.write("* Historical data depth and VIX data availability may be limited by the free API tier. Consider using a VIX proxy ETF symbol (like VXX) if direct VIX data is unavailable.")
            st.write("* API call frequency limits apply to the free tier. Be mindful of usage.")
            st.write("* Regime classifications are based on predefined thresholds and rules, which are examples and can be adjusted and optimized through backtesting.")
            st.write("* **Do not make investment decisions based solely on this indicator.** Consult with a qualified financial advisor before making any investment decisions.")


if __name__ == "__main__":
    main()
