"""
components/tab_chart.py
=======================
"Price Chart" tab — candlestick with optional MAs, ATH/ATL markers, volume.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from config.settings import CANDLESTICK_FALLING_COLOR, CANDLESTICK_RISING_COLOR, MA_COLORS, CHART_TEMPLATE


def render_price_chart(
    df: pd.DataFrame,
    symbol: str,
    show_volume: bool,
    show_ma: bool,
    ma_periods: list[int],
) -> None:
    """Render the interactive candlestick chart."""

    st.markdown("### Interactive Price Chart")

    rows = 2 if show_volume else 1
    row_heights = [0.7, 0.3] if show_volume else [1.0]

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=row_heights,
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
            increasing_line_color=CANDLESTICK_RISING_COLOR,
            decreasing_line_color=CANDLESTICK_FALLING_COLOR,
        ),
        row=1, col=1,
    )

    # Moving averages
    if show_ma:
        for i, period in enumerate(ma_periods):
            if len(df) >= period:
                ma = df["Close"].rolling(window=period).mean()
                fig.add_trace(
                    go.Scatter(
                        x=df["Date"],
                        y=ma,
                        mode="lines",
                        name=f"MA{period}",
                        line=dict(color=MA_COLORS[i % len(MA_COLORS)], width=1.5),
                        opacity=0.8,
                    ),
                    row=1, col=1,
                )

    # ATH / ATL markers
    ath_idx = df["High"].idxmax()
    atl_idx = df["Low"].idxmin()

    fig.add_trace(
        go.Scatter(
            x=[df.loc[ath_idx, "Date"]],
            y=[df.loc[ath_idx, "High"]],
            mode="markers",
            name=f'ATH: Rs. {df.loc[ath_idx, "High"]:.2f}',
            marker=dict(size=15, color="#2ca02c", symbol="triangle-up"),
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[df.loc[atl_idx, "Date"]],
            y=[df.loc[atl_idx, "Low"]],
            mode="markers",
            name=f'ATL: Rs. {df.loc[atl_idx, "Low"]:.2f}',
            marker=dict(size=15, color="#d62728", symbol="triangle-down"),
        ),
        row=1, col=1,
    )

    # Volume bars
    if show_volume:
        vol_colors = [
            CANDLESTICK_RISING_COLOR if df["Close"].iloc[i] >= df["Open"].iloc[i]
            else CANDLESTICK_FALLING_COLOR
            for i in range(len(df))
        ]
        fig.add_trace(
            go.Bar(
                x=df["Date"],
                y=df["Volume"],
                name="Volume",
                marker_color=vol_colors,
                opacity=0.6,
            ),
            row=2, col=1,
        )

    fig.update_layout(
        title=f"{symbol} — Price History",
        xaxis_title="Date",
        yaxis_title="Price (Rs.)",
        height=600 if show_volume else 500,
        template=CHART_TEMPLATE,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(rangeslider_visible=False)

    st.plotly_chart(fig, width='stretch')
