import streamlit as st
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import plotly.express as px

st.title("SPY Historical Data Dashboard")

# Input box for Alpha Vantage API token
api_token = st.text_input("Enter your Alpha Vantage API Token:", type="password")

if api_token:
    try:
        # Initialize Alpha Vantage Time Series API
        ts = TimeSeries(key=api_token, output_format='pandas')

        # Fetch daily historical data for SPY
        data, meta_data = ts.get_daily(symbol='SPY', outputsize='full') # outputsize='full' for max historical data

        if data is not None and not data.empty:
            st.success("Data fetched successfully!")

            # Rename columns for better readability
            data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            data.index.name = 'Date'

            # Display raw data (optional)
            if st.checkbox("Show Raw Data"):
                st.write(data)

            # Calculate Moving Averages
            data['MA10'] = data['Close'].rolling(window=10).mean()
            data['MA20'] = data['Close'].rolling(window=20).mean()
            data['MA50'] = data['Close'].rolling(window=50).mean()

            # Plotting the closing price with Moving Averages
            st.subheader("SPY Closing Price with Moving Averages")
            fig_close = px.line(data, y=['Close', 'MA10', 'MA20', 'MA50'],
                                labels={'value': 'Price', 'Date': 'Date', 'variable': 'Legend'},
                                title="SPY Closing Price with 10, 20, and 50-Day Moving Averages")
            st.plotly_chart(fig_close, use_container_width=True)


            # Optional: Add more plots or analysis here (e.g., OHLC chart)

        else:
            st.error("Could not retrieve data for SPY. Please check your API token and ticker symbol.")

    except ValueError as e:
        st.error(f"Error fetching data: {e}. Please check your API token.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

else:
    st.warning("Please enter your Alpha Vantage API Token to fetch data.")

st.markdown("""
**Note:**

*   This dashboard uses the **non-premium** Alpha Vantage API. Be mindful of API request limits.
*   Get your free API token from [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key).
*   For extensive historical data, `outputsize='full'` is used, which might take longer for the initial fetch.
*   Consider caching the data for better performance if you plan to use this frequently.
""")
