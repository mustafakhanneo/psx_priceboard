"""
components/tab_technical.py
===========================
"Technical Analysis" tab — support/resistance, MAs, price-vs-MA chart, volume chart.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config.settings import CHART_TEMPLATE, MA_COLORS
from utils.analysis import get_moving_averages, get_support_resistance


def render_technical_tab(df: pd.DataFrame, current_price: float) -> dict[str, float]:
    """
    Render the technical-analysis tab.

    Returns the moving-averages dict so the caller can reuse it
    (e.g. in the export tab).
    """
    st.markdown("### Technical Indicators")

    sr = get_support_resistance(df, window=20)
    mas = get_moving_averages(df)

    _render_support_resistance(sr, current_price)
    _render_moving_averages(mas, current_price)

    st.markdown("---")
    _render_price_vs_ma_chart(df, mas)
    _render_volume_chart(df)

    return mas


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render_support_resistance(sr: dict[str, float], current_price: float) -> None:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Support & Resistance (20-day)")
        support    = sr["support"]
        resistance = sr["resistance"]
        span = resistance - support
        position = (current_price - support) / span if span else 0.5

        st.metric("Support",            f"Rs. {support:,.2f}")
        st.metric("Resistance",         f"Rs. {resistance:,.2f}")
        st.metric("Position in Range",  f"{position * 100:.1f}%")
        st.progress(float(min(max(position, 0), 1)))


def _render_moving_averages(mas: dict[str, float], current_price: float) -> None:
    _, col2 = st.columns(2)

    with col2:
        st.markdown("#### Moving Averages")
        for ma_name, ma_val in mas.items():
            diff     = current_price - ma_val
            diff_pct = (diff / ma_val) * 100
            delta_color = (
                "normal"  if abs(diff_pct) < 5
                else "inverse" if diff > 0
                else "off"
            )
            st.metric(
                ma_name,
                f"Rs. {ma_val:,.2f}",
                f"{diff:+.2f} ({diff_pct:+.2f}%)",
                delta_color=delta_color,
            )


def _render_price_vs_ma_chart(df: pd.DataFrame, mas: dict[str, float]) -> None:
    st.markdown("#### Price vs Moving Averages")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Close"],
            mode="lines",
            name="Close Price",
            line=dict(color="#1f77b4", width=2),
        )
    )

    for i, ma_name in enumerate(mas):
        period = int(ma_name.replace("MA", ""))
        if len(df) >= period:
            ma_series = df["Close"].rolling(window=period).mean()
            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=ma_series,
                    mode="lines",
                    name=ma_name,
                    line=dict(color=MA_COLORS[i % len(MA_COLORS)], width=1.5),
                    opacity=0.8,
                )
            )

    fig.update_layout(
        title="Price with Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price (Rs.)",
        template=CHART_TEMPLATE,
        height=500,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, width='stretch')


def _render_volume_chart(df: pd.DataFrame) -> None:
    st.markdown("#### Volume Analysis")

    vol_ma20 = df["Volume"].rolling(window=20).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["Date"],
            y=df["Volume"],
            name="Volume",
            marker_color="rgba(31, 119, 180, 0.5)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=vol_ma20,
            mode="lines",
            name="Volume MA20",
            line=dict(color="#ff7f0e", width=2),
        )
    )
    fig.update_layout(
        title="Volume with 20-day Moving Average",
        xaxis_title="Date",
        yaxis_title="Volume",
        template=CHART_TEMPLATE,
        height=400,
    )
    st.plotly_chart(fig, width='stretch')
