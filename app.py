import streamlit as st
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import plotly.express as px

st.title("SPY Historical Data Dashboard")

# Sidebar for inputs
with st.sidebar:
    st.header("Input Parameters")
    # API Token Input
    api_token = st.text_input("Alpha Vantage API Token:", type="password")

    # Moving Average Periods Input
    ma_periods = st.multiselect(
        "Moving Average Periods (days):",
        options=[10, 20, 50, 100, 200],
        default=[10, 20, 50],
    )


if api_token:
    try:
        # Initialize Alpha Vantage Time Series API
        ts = TimeSeries(key=api_token, output_format='pandas')

        # Fetch daily historical data for SPY
        data, meta_data = ts.get_daily(symbol='SPY', outputsize='full')  # outputsize='full' for max historical data

        if data is not None and not data.empty:
            st.success("Data fetched successfully!")

            # Rename columns for better readability
            data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            data.index.name = 'Date'

            # Date Range Slider
            min_date = data.index.min()
            max_date = data.index.max()
            start_date, end_date = st.sidebar.slider(
                "Select Date Range:",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),  # Default to full range
                format="YYYY-MM-DD"
            )

            # Filter data by date range
            filtered_data = data.loc[start_date:end_date]

            # Display raw data (optional)
            if st.sidebar.checkbox("Show Raw Data", value=False): # Moved checkbox to sidebar
                st.write(filtered_data)

            # Calculate Moving Averages based on user input
            ma_columns_to_plot = ['Close']
            for period in ma_periods:
                ma_column_name = f'MA{period}'
                filtered_data[ma_column_name] = filtered_data['Close'].rolling(window=period).mean()
                ma_columns_to_plot.append(ma_column_name)

            # Plotting the closing price with Moving Averages
            st.subheader("SPY Closing Price with Moving Averages")
            fig_close = px.line(filtered_data, y=ma_columns_to_plot,
                                labels={'value': 'Price', 'Date': 'Date', 'variable': 'Legend'},
                                title="SPY Closing Price with Moving Averages")
            st.plotly_chart(fig_close, use_container_width=True)


        else:
            st.error("Could not retrieve data for SPY. Please check your API token and ticker symbol.")

    except ValueError as e:
        st.error(f"Error fetching data: {e}. Please check your API token.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

else:
    st.warning("Please enter your Alpha Vantage API Token to fetch data in the sidebar.")

st.markdown("""
**Note:**

*   This dashboard uses the **non-premium** Alpha Vantage API. Be mindful of API request limits.
*   Get your free API token from [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key).
*   For extensive historical data, `outputsize='full'` is used, which might take longer for the initial fetch.
*   Consider caching the data for better performance if you plan to use this frequently.
""")
