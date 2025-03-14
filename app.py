import streamlit as st
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Import graph_objects for more control

# Set page layout to wide to make the chart larger
st.set_page_config(layout="wide")

st.title("SPY Historical Data Dashboard")

# Sidebar for inputs
with st.sidebar:
    st.header("Input Parameters")
    # API Token Input
    api_token = st.text_input("Alpha Vantage API Token:", type="password")

    # Moving Average Period Input (Single Input Now)
    ma_period = st.number_input("Moving Average Period (days):", min_value=2, max_value=200, value=20) # Default to 20-day MA

    # Input for Last N Days
    n_days = st.number_input("Show Last N Days:", min_value=1, max_value=3650, value=365) # Max 10 years as a reasonable limit


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

            # Ensure index is DatetimeIndex (just in case)
            if not isinstance(data.index, pd.DatetimeIndex):
                data.index = pd.to_datetime(data.index)

            # Calculate Moving Average on the *full* dataset (only one MA now)
            ma_column_name = f'MA{ma_period}'
            data[ma_column_name] = data['Close'].rolling(window=ma_period).mean().shift(-ma_period + 1)


            # --- LAST N DAYS FILTERING ---
            latest_date = data.index.max()
            start_date = latest_date - pd.Timedelta(days=n_days)
            filtered_data = data[data.index >= start_date].copy() # Boolean indexing and create a copy
            # --- END LAST N DAYS FILTERING ---


            # Determine Price Color based on the single MA
            ma_color_column = f'MA{ma_period}'
            filtered_data['Price_Color'] = filtered_data.apply(
                lambda row: 'green' if row['Close'] > row[ma_color_column] else 'red', axis=1
            )

            # Display raw data (optional) - display filtered data
            if st.sidebar.checkbox("Show Raw Data", value=False): # Moved checkbox to sidebar
                st.write(filtered_data)

            # Plotting the closing price with Moving Average - plot filtered data
            st.subheader(f"SPY Closing Price with {ma_period}-Day Moving Average (Color based on MA)")
            fig_close = go.Figure() # Use go.Figure for more control

            # --- Plotting Colored Price Line in Segments - CONNECTED LINES ---
            price_color_series = filtered_data['Price_Color']
            close_price_series = filtered_data['Close']

            last_color = price_color_series.iloc[0] # Initialize with first color
            start_index = 0

            for i in range(1, len(price_color_series)):
                current_color = price_color_series.iloc[i]
                if current_color != last_color:
                    # Add a trace for the segment with the last color - EXTEND TO CURRENT INDEX
                    fig_close.add_trace(go.Scatter(
                        x=filtered_data.index[start_index:i+1], # Extend to index i+1
                        y=close_price_series.iloc[start_index:i+1], # Extend to index i+1
                        mode='lines',
                        line=dict(color=last_color, width=1.5),
                        showlegend=False # Only show legend for the first segment
                    ))
                    start_index = i # Start new segment from current index
                    last_color = current_color # Update last color

            # Add the last segment - EXTEND TO THE END
            fig_close.add_trace(go.Scatter(
                x=filtered_data.index[start_index:], # Extend to the end
                y=close_price_series.iloc[start_index:], # Extend to the end
                mode='lines',
                line=dict(color=last_color, width=1.5),
                name='Close Price' # Show legend for the last segment (which is effectively the entire price line's legend)
            ))
            # --- End Plotting Colored Price Line in Segments - CONNECTED LINES ---


            # Add the Single Moving Average
            fig_close.add_trace(go.Scatter(
                x=filtered_data.index,
                y=filtered_data[ma_column_name],
                mode='lines',
                name=ma_column_name,
                line=dict(color='blue', dash='dash', width=1) # Example style for MA
            ))


            fig_close.update_layout(
                title=f"SPY Closing Price with {ma_period}-Day Moving Average (Color based on MA)",
                xaxis_title="Date",
                yaxis_title="Price",
                height=900 # Set a fixed height in pixels - adjust as needed
            )
            st.plotly_chart(fig_close, use_container_width=True) # Keep use_container_width=True

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
