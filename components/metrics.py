"""
components/metrics.py
=====================
Top-row summary metric cards.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.analysis import PeriodStats


def render_metric_cards(
    df: pd.DataFrame,
    current_price: float,
    daily_change: float,
    daily_change_pct: float,
    all_time: PeriodStats,
) -> None:
    """Render the five KPI cards at the top of the page."""

    cols = st.columns(5)

    # Current price
    with cols[0]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">Rs. {current_price:,.2f}</div>
                <div class="metric-label">Current Price</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Daily change
    with cols[1]:
        pos = daily_change >= 0
        grad = (
            "linear-gradient(135deg, #28a745 0%, #20c997 100%)"
            if pos
            else "linear-gradient(135deg, #dc3545 0%, #c82333 100%)"
        )
        sign = "+" if pos else ""
        st.markdown(
            f"""
            <div class="metric-card" style="background: {grad};">
                <div class="metric-value">{sign}{daily_change:,.2f}</div>
                <div class="metric-label">Daily Change ({sign}{daily_change_pct:.2f}%)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # All-time high
    with cols[2]:
        st.markdown(
            f"""
            <div class="metric-card"
                 style="background: linear-gradient(135deg, #2ca02c 0%, #98df8a 100%);">
                <div class="metric-value">Rs. {all_time["high"]:,.2f}</div>
                <div class="metric-label">All-Time High</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # All-time low
    with cols[3]:
        st.markdown(
            f"""
            <div class="metric-card"
                 style="background: linear-gradient(135deg, #d62728 0%, #ff9896 100%);">
                <div class="metric-value">Rs. {all_time["low"]:,.2f}</div>
                <div class="metric-label">All-Time Low</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Latest volume
    with cols[4]:
        volume = int(df.iloc[-1]["Volume"]) if "Volume" in df.columns else 0
        st.markdown(
            f"""
            <div class="metric-card"
                 style="background: linear-gradient(135deg, #ff7f0e 0%, #ffbb78 100%);">
                <div class="metric-value">{volume:,.0f}</div>
                <div class="metric-label">Current Volume</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
