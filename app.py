"""
app.py
======
PSX Price Tracker — main Streamlit entrypoint.

Run with:
    streamlit run app.py

This file is intentionally thin: it wires together config, data, and
components. Business logic lives in utils/; UI logic lives in components/.
"""

import streamlit as st

from config.settings import APP_ICON, APP_SUBTITLE, APP_TITLE, TIMEFRAME_WINDOWS
from config.styles import APP_CSS
from components.metrics import render_metric_cards
from components.sidebar import render_sidebar
from components.tab_chart import render_price_chart
from components.tab_export import render_export_tab
from components.tab_technical import render_technical_tab
from components.tab_timeframe import render_timeframe_tab
from utils.analysis import get_price_stats
from utils.data import fetch_psx_data, validate_and_fix_data, fetch_current_price

# ---------------------------------------------------------------------------
# Page config (must be the very first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(APP_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — collect all user options
# ---------------------------------------------------------------------------
opts = render_sidebar()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(f'<div class="main-header">{APP_ICON} {APP_TITLE}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{APP_SUBTITLE}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
with st.spinner(f"Loading {opts.symbol} data…"):
    raw_df, data_source = fetch_psx_data(opts.symbol, opts.start_date, opts.end_date)
    df = validate_and_fix_data(raw_df)

if data_source == "sample":
    st.warning(
        "Using **sample data** for demonstration.  \n"
        "Install live data: `pip install psxdata>=0.1.0a3`"
    )
else:
    st.success("Live data fetched from **psxdata**!")

if df is None or len(df) == 0:
    st.error("No data available. Please check the symbol and date range.")
    st.stop()

# ---------------------------------------------------------------------------
# Derived metrics (computed once, passed to components)
# ---------------------------------------------------------------------------
quote = fetch_current_price(opts.symbol)
current_price   = quote if quote is not None else float(df.iloc[-1]["Close"])
prev_close      = float(df.iloc[-2]["Close"]) if len(df) > 1 else current_price
daily_change    = current_price - prev_close
daily_change_pct = (daily_change / prev_close) * 100

all_time    = get_price_stats(df)
timeframes  = {label: get_price_stats(df, days) for label, days in TIMEFRAME_WINDOWS.items()}

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
st.markdown("---")
render_metric_cards(df, current_price, daily_change, daily_change_pct, all_time)
st.markdown("---")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_chart, tab_tf, tab_tech, tab_export = st.tabs(
    ["📊 Price Chart", "📅 Timeframe Analysis", "🔬 Technical Analysis", "💾 Export Data"]
)

with tab_chart:
    render_price_chart(
        df,
        symbol=opts.symbol,
        show_volume=opts.show_volume,
        show_ma=opts.show_ma,
        ma_periods=opts.ma_periods,
    )

with tab_tf:
    render_timeframe_tab(df)

with tab_tech:
    moving_averages = render_technical_tab(df, current_price)

with tab_export:
    render_export_tab(
        df,
        symbol=opts.symbol,
        current_price=current_price,
        daily_change=daily_change,
        daily_change_pct=daily_change_pct,
        all_time=all_time,
        timeframes=timeframes,
        moving_averages=moving_averages,
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; color:#666; font-size:0.9rem;">
        <p>PSX Price Tracker | Data sourced from Pakistan Stock Exchange</p>
        <p>Built with Streamlit &amp; Plotly | Powered by psxdata library</p>
    </div>
    """,
    unsafe_allow_html=True,
)
