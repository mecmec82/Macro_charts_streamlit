import streamlit as st
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Import graph_objects for more control

st.title("SPY Historical Data Dashboard")

# Sidebar for inputs
with st.sidebar:
    st.header("Input Parameters")
    # API Token Input
    api_token = st.text_input("Alpha Vantage API Token:", type="password")

    # Moving Average Periods Input
    ma_periods_options = [10, 20, 50, 100, 200] # Define options list
    ma_periods = st.multiselect(
        "Moving Average Periods (days):",
        options=ma_periods_options,
        default=[10, 20, 50],
    )

    # Input for Last N Days
    n_days = st.number_input("Show Last N Days:", min_value=1, max_value=3650, value=365) # Max 10 years as a reasonable limit

    # Select MA for Price Color
    ma_period_color = st.selectbox("MA for Price Color:", options=ma_periods, index=1 if len(ma_periods) > 1 else 0) # Default to 20-day MA, or first if less than 2


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

            # Calculate Moving Averages on the *full* dataset
            ma_columns_to_plot = ['Close'] # Still want to plot Close, but as separate traces now
            for period in ma_periods:
                ma_column_name = f'MA{period}'
                # Calculate MA and shift to align to the end of the period on the *full data*
                data[ma_column_name] = data['Close'].rolling(window=period).mean().shift(-period + 1)
                ma_columns_to_plot.append(ma_column_name)


            # --- LAST N DAYS FILTERING ---
            latest_date = data.index.max()
            start_date = latest_date - pd.Timedelta(days=n_days)
            filtered_data = data[data.index >= start_date].copy() # Boolean indexing and create a copy
            # --- END LAST N DAYS FILTERING ---


            # Determine Price Color based on selected MA
            ma_color_column = f'MA{ma_period_color}'
            filtered_data['Price_Color'] = filtered_data.apply(
                lambda row: 'green' if row['Close'] > row[ma_color_column] else 'red', axis=1
            )

            # Display raw data (optional) - display filtered data
            if st.sidebar.checkbox("Show Raw Data", value=False): # Moved checkbox to sidebar
                st.write(filtered_data)

            # Plotting the closing price with Moving Averages - plot filtered data
            st.subheader("SPY Closing Price with Moving Averages (Color based on MA)")
            fig_close = go.Figure() # Use go.Figure for more control

            # --- Plotting Colored Price Line in Segments ---
            price_color_series = filtered_data['Price_Color']
            close_price_series = filtered_data['Close']

            last_color = price_color_series.iloc[0] # Initialize with first color
            start_index = 0

            for i in range(1, len(price_color_series)):
                current_color = price_color_series.iloc[i]
                if current_color != last_color:
                    # Add a trace for the segment with the last color
                    fig_close.add_trace(go.Scatter(
                        x=filtered_data.index[start_index:i],
                        y=close_price_series.iloc[start_index:i],
                        mode='lines',
                        line=dict(color=last_color, width=1.5),
                        showlegend=False # Only show legend for the first segment
                    ))
                    start_index = i # Start new segment from current index
                    last_color = current_color # Update last color

            # Add the last segment
            fig_close.add_trace(go.Scatter(
                x=filtered_data.index[start_index:],
                y=close_price_series.iloc[start_index:],
                mode='lines',
                line=dict(color=last_color, width=1.5),
                name='Close Price' # Show legend for the last segment (which is effectively the entire price line's legend)
            ))
            # --- End Plotting Colored Price Line in Segments ---


            # Add Moving Averages as separate traces
            for ma_col in [col for col in ma_columns_to_plot if col != 'Close']: # Plot MAs, excluding 'Close' from ma_columns_to_plot
                fig_close.add_trace(go.Scatter(
                    x=filtered_data.index,
                    y=filtered_data[ma_col],
                    mode='lines',
                    name=ma_col,
                    line=dict(color='blue', dash='dash', width=1) # Example style for MAs
                ))


            fig_close.update_layout(
                title="SPY Closing Price with Moving Averages (Color based on MA)",
                xaxis_title="Date",
                yaxis_title="Price"
            )
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
