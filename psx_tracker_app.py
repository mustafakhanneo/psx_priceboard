
"""
PSX (Pakistan Stock Exchange) Price Tracker - Streamlit GUI
=============================================================
Beautiful interactive web app for tracking Pakistan Stock Exchange stocks.

Uses psxdata>=0.1.0a3 as primary data source (psx is under construction).

Installation:
    pip install streamlit plotly pandas numpy psxdata>=0.1.0a3 openpyxl

Run with:
    streamlit run psx_tracker_app.py

Data Source:
    - psxdata (PyPI): pip install psxdata>=0.1.0a3
    - GitHub: https://github.com/mtauha/psxdata
    - By: Muhammad Tauha (mtauha)
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import json
import os

# Page config
st.set_page_config(
    page_title="PSX Price Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .positive { color: #28a745; font-weight: bold; }
    .negative { color: #dc3545; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 4px;
    }
    .dataframe th {
        background-color: #f8f9fa;
        color: #333;
        font-weight: 600;
    }
    .dataframe td {
        text-align: right;
    }
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== PSX DATA FETCHER ====================

@st.cache_data(ttl=3600)
def fetch_psx_data(symbol, start_date, end_date):
    """
    Fetch PSX data using psxdata>=0.1.0a3 (primary source).
    Falls back to sample data if psxdata is not installed.
    """
    # Try psxdata first (primary source)
    try:
        import psxdata
        df = psxdata.stocks(symbol, start=str(start_date), end=str(end_date))
        if df is not None and len(df) > 0:
            df = df.reset_index()
            # Standardize column names
            df.columns = [c.strip().title() for c in df.columns]
            if 'Date' not in df.columns:
                date_cols = [c for c in df.columns if 'date' in c.lower()]
                if date_cols:
                    df.rename(columns={date_cols[0]: 'Date'}, inplace=True)
            return df, "psxdata"
    except Exception as e:
        st.warning(f"psxdata not available: {e}")

    # Fallback: generate sample data
    return generate_sample_data(symbol, start_date, end_date), "sample"


def generate_sample_data(symbol, start_date, end_date):
    """Generate realistic sample PSX data for demo"""
    np.random.seed(hash(symbol) % 10000)

    date_range = pd.date_range(start=start_date, end=end_date, freq='B')
    n_days = len(date_range)

    base_prices = {
        'HBL': 150, 'OGDC': 80, 'ENGRO': 200, 'LUCK': 350,
        'MCB': 120, 'PPL': 90, 'UNITY': 25, 'TRG': 45,
        'SILK': 15, 'PACE': 10, 'KEL': 3, 'PIAA': 5
    }
    base = base_prices.get(symbol, 100)

    returns = np.random.normal(0.0003, 0.015, n_days)
    prices = base * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'Date': date_range,
        'Open': prices * (1 + np.random.normal(0, 0.005, n_days)),
        'High': prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
        'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
        'Close': prices,
        'Volume': np.random.randint(100000, 5000000, n_days)
    })

    # Ensure OHLC constraints: High >= max(Open, Close), Low <= min(Open, Close)
    for i in range(len(df)):
        df.loc[i, 'High'] = max(df.loc[i, 'High'], df.loc[i, 'Open'], df.loc[i, 'Close'])
        df.loc[i, 'Low'] = min(df.loc[i, 'Low'], df.loc[i, 'Open'], df.loc[i, 'Close'])

    return df


def validate_and_fix_data(df):
    """
    Validate and fix common data issues:
    1. Ensure chronological order
    2. Fix OHLC constraints (High >= Open/Close, Low <= Open/Close)
    3. Remove duplicate dates
    4. Ensure numeric columns
    """
    if df is None or len(df) == 0:
        return df

    # Make a copy to avoid modifying original
    df = df.copy()

    # Ensure Date is datetime
    df['Date'] = pd.to_datetime(df['Date'])

    # Sort by date to ensure chronological order
    df = df.sort_values('Date').reset_index(drop=True)

    # Remove duplicate dates (keep first)
    df = df.drop_duplicates(subset=['Date'], keep='first').reset_index(drop=True)

    # Ensure numeric columns
    numeric_cols = ['Open', 'High', 'Low', 'Close']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Volume' in df.columns:
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0).astype(int)

    # Fix OHLC constraints
    for i in range(len(df)):
        # High must be >= Open, Close
        max_oc = max(df.loc[i, 'Open'], df.loc[i, 'Close'])
        if df.loc[i, 'High'] < max_oc:
            df.loc[i, 'High'] = max_oc

        # Low must be <= Open, Close
        min_oc = min(df.loc[i, 'Open'], df.loc[i, 'Close'])
        if df.loc[i, 'Low'] > min_oc:
            df.loc[i, 'Low'] = min_oc

    return df


# ==================== ANALYSIS FUNCTIONS ====================

def get_price_stats(df, days=None):
    """Calculate price statistics for a given period"""
    if days is not None:
        end_date = df['Date'].max()
        start = end_date - timedelta(days=days)
        mask = (df['Date'] >= start) & (df['Date'] <= end_date)
        df = df[mask]

    if len(df) == 0:
        return None

    return {
        'high': df['High'].max(),
        'low': df['Low'].min(),
        'high_date': df.loc[df['High'].idxmax(), 'Date'],
        'low_date': df.loc[df['Low'].idxmin(), 'Date'],
        'open': df.iloc[0]['Open'],
        'close': df.iloc[-1]['Close'],
        'volume': int(df['Volume'].sum()) if 'Volume' in df.columns else 0,
        'change_pct': ((df.iloc[-1]['Close'] - df.iloc[0]['Open']) / df.iloc[0]['Open']) * 100,
        'days': len(df)
    }


def get_moving_averages(df):
    """Calculate moving averages"""
    close = df['Close']
    mas = {}
    for period in [5, 10, 20, 50, 100, 200]:
        if len(close) >= period:
            mas[f'MA{period}'] = close.rolling(window=period).mean().iloc[-1]
    return mas


# ==================== SIDEBAR ====================

with st.sidebar:
    st.markdown("## PSX Tracker")
    st.markdown("---")

    # Stock selection
    st.markdown("### Select Stock")

    popular_stocks = {
        'HBL': 'Habib Bank Limited',
        'OGDC': 'Oil & Gas Development Company',
        'ENGRO': 'Engro Corporation',
        'LUCK': 'Lucky Cement',
        'MCB': 'MCB Bank Limited',
        'PPL': 'Pakistan Petroleum Limited',
        'UNITY': 'Unity Foods',
        'TRG': 'TRG Pakistan',
        'SILK': 'Silk Bank Limited',
        'KEL': 'K-Electric Limited'
    }

    stock_option = st.selectbox(
        "Choose a stock",
        options=list(popular_stocks.keys()),
        format_func=lambda x: f"{x} - {popular_stocks[x]}"
    )

    custom_symbol = st.text_input("Or enter custom symbol", "")
    symbol = custom_symbol.upper() if custom_symbol else stock_option

    st.markdown("---")

    # Date range
    st.markdown("### Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start", date.today() - timedelta(days=1095))
    with col2:
        end_date = st.date_input("End", date.today())

    st.markdown("---")

    # Quick ranges
    st.markdown("### Quick Select")
    quick_range = st.selectbox(
        "Preset ranges",
        ["Custom", "1 Month", "3 Months", "6 Months", "1 Year", "3 Years", "5 Years", "All Time"]
    )

    if quick_range == "1 Month":
        start_date = date.today() - timedelta(days=30)
    elif quick_range == "3 Months":
        start_date = date.today() - timedelta(days=90)
    elif quick_range == "6 Months":
        start_date = date.today() - timedelta(days=180)
    elif quick_range == "1 Year":
        start_date = date.today() - timedelta(days=365)
    elif quick_range == "3 Years":
        start_date = date.today() - timedelta(days=1095)
    elif quick_range == "5 Years":
        start_date = date.today() - timedelta(days=1825)
    elif quick_range == "All Time":
        start_date = date(2015, 1, 1)

    st.markdown("---")

    # Settings
    st.markdown("### Settings")
    show_volume = st.checkbox("Show Volume", value=True)
    show_ma = st.checkbox("Show Moving Averages", value=True)
    ma_periods = st.multiselect(
        "MA Periods",
        [5, 10, 20, 50, 100, 200],
        default=[20, 50, 200]
    )

    st.markdown("---")
    st.markdown("Made with love for PSX Investors")


# ==================== MAIN CONTENT ====================

st.markdown('<div class="main-header">PSX Price Tracker</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Pakistan Stock Exchange - Comprehensive Stock Analysis</div>', unsafe_allow_html=True)

# Fetch data
with st.spinner(f"Loading {symbol} data..."):
    df, data_source = fetch_psx_data(symbol, start_date, end_date)

    # Validate and fix data issues
    df = validate_and_fix_data(df)

# Show data source info
if data_source == "sample":
    st.warning("""
    Using **sample data** for demonstration. 

    To get **live PSX data**, install psxdata:
    ```
    pip install psxdata>=0.1.0a3
    ```
    """)
else:
    st.success(f"Live data fetched from **psxdata** library!")

if df is None or len(df) == 0:
    st.error("No data available. Please check the symbol and date range.")
    st.stop()

# Calculate metrics
current_price = df.iloc[-1]['Close']
prev_close = df.iloc[-2]['Close'] if len(df) > 1 else current_price
daily_change = current_price - prev_close
daily_change_pct = (daily_change / prev_close) * 100

all_time = get_price_stats(df)
timeframes = {
    'Daily (1D)': get_price_stats(df, 1),
    '3 Days': get_price_stats(df, 3),
    'Weekly (7D)': get_price_stats(df, 7),
    '15 Days': get_price_stats(df, 15),
    'Monthly (30D)': get_price_stats(df, 30),
    '3 Months (90D)': get_price_stats(df, 90),
    '6 Months (180D)': get_price_stats(df, 180),
    '9 Months (270D)': get_price_stats(df, 270),
    'Yearly (365D)': get_price_stats(df, 365),
    '3 Years (1095D)': get_price_stats(df, 1095),
}

# TOP METRICS CARDS
st.markdown("---")
cols = st.columns(5)

with cols[0]:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">Rs. {current_price:,.2f}</div>
        <div class="metric-label">Current Price</div>
    </div>
    """, unsafe_allow_html=True)

with cols[1]:
    change_class = "positive" if daily_change >= 0 else "negative"
    sign = "+" if daily_change >= 0 else ""
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, {'#28a745' if daily_change >= 0 else '#dc3545'} 0%, {'#20c997' if daily_change >= 0 else '#c82333'} 100%);">
        <div class="metric-value">{sign}{daily_change:,.2f}</div>
        <div class="metric-label">Daily Change ({sign}{daily_change_pct:.2f}%)</div>
    </div>
    """, unsafe_allow_html=True)

with cols[2]:
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #2ca02c 0%, #98df8a 100%);">
        <div class="metric-value">Rs. {all_time['high']:,.2f}</div>
        <div class="metric-label">All-Time High</div>
    </div>
    """, unsafe_allow_html=True)

with cols[3]:
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #d62728 0%, #ff9896 100%);">
        <div class="metric-value">Rs. {all_time['low']:,.2f}</div>
        <div class="metric-label">All-Time Low</div>
    </div>
    """, unsafe_allow_html=True)

with cols[4]:
    volume = int(df.iloc[-1]['Volume']) if 'Volume' in df.columns else 0
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #ff7f0e 0%, #ffbb78 100%);">
        <div class="metric-value">{volume:,.0f}</div>
        <div class="metric-label">Volume</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# TABS
tab1, tab2, tab3, tab4 = st.tabs(["Price Chart", "Timeframe Analysis", "Technical Analysis", "Export Data"])

# TAB 1: PRICE CHART
with tab1:
    st.markdown("### Interactive Price Chart")

    fig = make_subplots(
        rows=2 if show_volume else 1,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.7, 0.3] if show_volume else [1]
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#28a745',
            decreasing_line_color='#dc3545'
        ),
        row=1, col=1
    )

    # Moving Averages
    if show_ma:
        colors_ma = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        for i, period in enumerate(ma_periods):
            if len(df) >= period:
                ma = df['Close'].rolling(window=period).mean()
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=ma,
                        mode='lines',
                        name=f'MA{period}',
                        line=dict(color=colors_ma[i % len(colors_ma)], width=1.5),
                        opacity=0.8
                    ),
                    row=1, col=1
                )

    # Mark ATH and ATL
    ath_idx = df['High'].idxmax()
    atl_idx = df['Low'].idxmin()

    fig.add_trace(
        go.Scatter(
            x=[df.loc[ath_idx, 'Date']],
            y=[df.loc[ath_idx, 'High']],
            mode='markers',
            name=f'ATH: Rs. {df.loc[ath_idx, "High"]:.2f}',
            marker=dict(size=15, color='#2ca02c', symbol='triangle-up')
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=[df.loc[atl_idx, 'Date']],
            y=[df.loc[atl_idx, 'Low']],
            mode='markers',
            name=f'ATL: Rs. {df.loc[atl_idx, "Low"]:.2f}',
            marker=dict(size=15, color='#d62728', symbol='triangle-down')
        ),
        row=1, col=1
    )

    # Volume
    if show_volume:
        colors_vol = ['#28a745' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#dc3545' 
                       for i in range(len(df))]
        fig.add_trace(
            go.Bar(
                x=df['Date'],
                y=df['Volume'],
                name='Volume',
                marker_color=colors_vol,
                opacity=0.6
            ),
            row=2, col=1
        )

    fig.update_layout(
        title=f'{symbol} - Price History',
        xaxis_title='Date',
        yaxis_title='Price (Rs.)',
        height=600 if show_volume else 500,
        template='plotly_white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    fig.update_xaxes(rangeslider_visible=False)

    # FIX: use_container_width -> width (Streamlit deprecation)
    st.plotly_chart(fig, width="stretch")

# TAB 2: TIMEFRAME ANALYSIS
with tab2:
    st.markdown("### Comprehensive Timeframe Analysis")

    # Create DataFrame for display
    tf_data = []
    for name, stats in timeframes.items():
        if stats:
            tf_data.append({
                'Timeframe': name,
                'High': f"Rs. {stats['high']:,.2f}",
                'Low': f"Rs. {stats['low']:,.2f}",
                'Change %': f"{stats['change_pct']:+.2f}%",
                'Trading Days': stats['days']
            })

    tf_df = pd.DataFrame(tf_data)

    # FIX: applymap -> map (pandas deprecation)
    def highlight_change(val):
        try:
            num = float(val.replace('%', '').replace('+', ''))
            if num > 0:
                return 'background-color: #d4edda; color: #155724'
            elif num < 0:
                return 'background-color: #f8d7da; color: #721c24'
        except:
            pass
        return ''

    st.dataframe(
        tf_df.style.map(highlight_change, subset=['Change %']),
        width="stretch",
        hide_index=True
    )

    # High/Low comparison chart
    st.markdown("### High/Low Comparison by Timeframe")

    chart_data = []
    for name, stats in timeframes.items():
        if stats:
            chart_data.append({
                'Timeframe': name,
                'Price': stats['high'],
                'Type': 'High'
            })
            chart_data.append({
                'Timeframe': name,
                'Price': stats['low'],
                'Type': 'Low'
            })

    chart_df = pd.DataFrame(chart_data)

    fig2 = px.bar(
        chart_df,
        x='Timeframe',
        y='Price',
        color='Type',
        barmode='group',
        color_discrete_map={'High': '#2ca02c', 'Low': '#d62728'},
        title='High vs Low by Timeframe',
        labels={'Price': 'Price (Rs.)', 'Timeframe': ''}
    )
    fig2.update_layout(template='plotly_white', height=400)
    st.plotly_chart(fig2, width="stretch")

    # Period returns
    st.markdown("### Period Returns")

    returns_data = []
    for name, stats in timeframes.items():
        if stats:
            returns_data.append({
                'Timeframe': name,
                'Return %': stats['change_pct']
            })

    returns_df = pd.DataFrame(returns_data)
    colors = ['#28a745' if x >= 0 else '#dc3545' for x in returns_df['Return %']]

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=returns_df['Timeframe'],
        y=returns_df['Return %'],
        marker_color=colors,
        text=[f"{x:+.2f}%" for x in returns_df['Return %']],
        textposition='auto'
    ))
    fig3.update_layout(
        title='Returns by Timeframe',
        yaxis_title='Return %',
        template='plotly_white',
        height=400
    )
    fig3.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig3, width="stretch")

# TAB 3: TECHNICAL ANALYSIS
with tab3:
    st.markdown("### Technical Indicators")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Support & Resistance (20-day)")
        recent = df.tail(20)
        support = recent['Low'].min()
        resistance = recent['High'].max()
        position = (current_price - support) / (resistance - support) if resistance != support else 0.5

        st.metric("Support", f"Rs. {support:,.2f}")
        st.metric("Resistance", f"Rs. {resistance:,.2f}")
        st.metric("Position in Range", f"{position*100:.1f}%")

        # Progress bar for position
        st.progress(min(max(position, 0), 1))

    with col2:
        st.markdown("#### Moving Averages")
        mas = get_moving_averages(df)

        for ma_name, ma_val in mas.items():
            diff = current_price - ma_val
            diff_pct = (diff / ma_val) * 100
            delta_color = "normal" if abs(diff_pct) < 5 else ("inverse" if diff > 0 else "off")
            st.metric(
                ma_name,
                f"Rs. {ma_val:,.2f}",
                f"{diff:+.2f} ({diff_pct:+.2f}%)",
                delta_color=delta_color
            )

    st.markdown("---")

    # Price vs MAs chart
    st.markdown("#### Price vs Moving Averages")

    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Close'],
        mode='lines',
        name='Close Price',
        line=dict(color='#1f77b4', width=2)
    ))

    colors_ma = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    for i, (ma_name, ma_val) in enumerate(mas.items()):
        period = int(ma_name.replace('MA', ''))
        if len(df) >= period:
            ma_series = df['Close'].rolling(window=period).mean()
            fig4.add_trace(go.Scatter(
                x=df['Date'],
                y=ma_series,
                mode='lines',
                name=ma_name,
                line=dict(color=colors_ma[i % len(colors_ma)], width=1.5),
                opacity=0.8
            ))

    fig4.update_layout(
        title='Price with Moving Averages',
        xaxis_title='Date',
        yaxis_title='Price (Rs.)',
        template='plotly_white',
        height=500,
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    st.plotly_chart(fig4, width="stretch")

    # Volume analysis
    st.markdown("#### Volume Analysis")

    df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()

    fig5 = go.Figure()
    fig5.add_trace(go.Bar(
        x=df['Date'],
        y=df['Volume'],
        name='Volume',
        marker_color='rgba(31, 119, 180, 0.5)'
    ))
    fig5.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Volume_MA20'],
        mode='lines',
        name='Volume MA20',
        line=dict(color='#ff7f0e', width=2)
    ))
    fig5.update_layout(
        title='Volume with 20-day Moving Average',
        xaxis_title='Date',
        yaxis_title='Volume',
        template='plotly_white',
        height=400
    )
    st.plotly_chart(fig5, width="stretch")

# TAB 4: EXPORT
with tab4:
    st.markdown("### Export Data & Reports")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### JSON Report")
        report_data = {
            'symbol': symbol,
            'current_price': current_price,
            'daily_change': daily_change,
            'daily_change_pct': daily_change_pct,
            'all_time_high': all_time['high'],
            'all_time_low': all_time['low'],
            'timeframes': {k: {
                'high': v['high'],
                'low': v['low'],
                'change_pct': v['change_pct']
            } for k, v in timeframes.items() if v},
            'moving_averages': {k: v for k, v in mas.items()}
        }

        json_str = json.dumps(report_data, indent=2, default=str)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name=f"{symbol}_report.json",
            mime="application/json"
        )

    with col2:
        st.markdown("#### CSV Data")
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"{symbol}_data.csv",
            mime="text/csv"
        )

    with col3:
        st.markdown("#### Raw Data Preview")
        st.dataframe(df.tail(10), width="stretch")

# FOOTER
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>PSX Price Tracker | Data sourced from Pakistan Stock Exchange</p>
    <p>Built with Streamlit & Plotly | Powered by psxdata library</p>
</div>
""", unsafe_allow_html=True)