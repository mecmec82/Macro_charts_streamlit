def fetch_sp500_data_alphavantage(symbol, api_key, period="1y"): # Using "1y" as period for simplicity
    """Fetches historical S&P 500 data from Alpha Vantage API (simplified) using TIME_SERIES_DAILY (unadjusted)."""
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={api_key}" # Changed to TIME_SERIES_DAILY

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if 'Time Series (Daily)' in data: # Adjusted key to 'Time Series (Daily)'
            time_series_data = data['Time Series (Daily)'] # Adjusted key to 'Time Series (Daily)'
            df = pd.DataFrame.from_dict(time_series_data, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            df.rename(columns={'4. close': 'Close'}, inplace=True)
            df['Close'] = pd.to_numeric(df['Close'])
            return df[['Close']]
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
