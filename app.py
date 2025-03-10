# E3AHZ2K13ICQR8FC   #alphavantage key

import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta

# --- Configuration ---
DEFAULT_SYMBOL = "SPY"  # SPDR S&P 500 ETF (using SPY for simplicity in this test)
LOOKBACK_DAYS = 365  # 1 year of data for this simplified example

# --- Data Fetching Function (Simplified for S&P 500) ---
def fetch_sp500_data_alphavantage(symbol, api_key, period="1y"): # Using "1y" as period for simplicity
    """Fetches historical S&P 500 data from Alpha Vantage API (simplified)."""
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=compact&apikey={api_key}" # Using 'compact' output for faster testing

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if 'Time Series (Daily Adjusted)' in data:
            time_series_data = data['Time Series (Daily Adjusted)']
            df = pd.DataFrame.from_dict(time_series_data, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            df.rename(columns={'4. close': 'Close'}, inplace=True) # Just get 'Close' price for simplicity
            df['Close'] = pd.to_numeric(df['Close']) # Ensure 'Close' is numeric
            return df[['Close']] # Return only the 'Close' column
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


# --- Streamlit App (Simplified) ---
def main():
    st.title("Simplified S&P 500 Chart (Alpha Vantage)")

    st.sidebar.header("Settings")
    alpha_vantage_api_key = st.sidebar.text_input("Alpha Vantage API Key", type="password")
    symbol = st.sidebar.text_input("Stock Symbol (e.g., SPY)", DEFAULT_SYMBOL)

    if st.sidebar.button("Get S&P 500 Chart"):
        if not alpha_vantage_api_key:
            st.sidebar.error("Please enter your Alpha Vantage API Key.")
            st.stop()

        with st.spinner(f"Fetching S&P 500 data for {symbol} from Alpha Vantage..."):
            end_date = datetime.today()
            start_date = end_date - timedelta(days=LOOKBACK_DAYS)
            # period_str is not used in this simplified version, we are using 'compact' output

            sp500_data = fetch_sp500_data_alphavantage(symbol, alpha_vantage_api_key)

            if sp500_data is not None and not sp500_data.empty:
                st.subheader(f"S&P 500 - {symbol} Price Chart")
                st.line_chart(sp500_data)
            else:
                st.error(f"Failed to retrieve S&P 500 data for symbol: {symbol}")
                st.info("Please check the symbol and your Alpha Vantage API key. Also, ensure Alpha Vantage supports this symbol.")


if __name__ == "__main__":
    main()
