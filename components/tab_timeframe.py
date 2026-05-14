"""
components/tab_timeframe.py
===========================
"Timeframe Analysis" tab — table, high/low bar chart, period-returns chart.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config.settings import CHART_TEMPLATE, TIMEFRAME_WINDOWS
from utils.analysis import PeriodStats, get_price_stats


def render_timeframe_tab(df: pd.DataFrame) -> None:
    """Render the full timeframe-analysis tab."""

    st.markdown("### Comprehensive Timeframe Analysis")

    # Build stats for each window
    timeframes: dict[str, PeriodStats | None] = {
        label: get_price_stats(df, days)
        for label, days in TIMEFRAME_WINDOWS.items()
    }

    _render_summary_table(timeframes)
    _render_high_low_chart(timeframes)
    _render_returns_chart(timeframes)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render_summary_table(timeframes: dict[str, PeriodStats | None]) -> None:
    rows = [
        {
            "Timeframe":    label,
            "High":         f"Rs. {s['high']:,.2f}",
            "Low":          f"Rs. {s['low']:,.2f}",
            "Change %":     f"{s['change_pct']:+.2f}%",
            "Trading Days": s["days"],
        }
        for label, s in timeframes.items()
        if s
    ]
    tf_df = pd.DataFrame(rows)

    st.dataframe(
        tf_df.style.map(_highlight_change, subset=["Change %"]),
        width='stretch',
        hide_index=True,
    )


def _highlight_change(val: str) -> str:
    try:
        num = float(val.replace("%", "").replace("+", ""))
        if num > 0:
            return "background-color: #d4edda; color: #155724"
        if num < 0:
            return "background-color: #f8d7da; color: #721c24"
    except ValueError:
        pass
    return ""


def _render_high_low_chart(timeframes: dict[str, PeriodStats | None]) -> None:
    st.markdown("### High / Low Comparison by Timeframe")

    rows = []
    for label, s in timeframes.items():
        if s:
            rows += [
                {"Timeframe": label, "Price": s["high"], "Type": "High"},
                {"Timeframe": label, "Price": s["low"],  "Type": "Low"},
            ]

    fig = px.bar(
        pd.DataFrame(rows),
        x="Timeframe",
        y="Price",
        color="Type",
        barmode="group",
        color_discrete_map={"High": "#2ca02c", "Low": "#d62728"},
        title="High vs Low by Timeframe",
        labels={"Price": "Price (Rs.)", "Timeframe": ""},
    )
    fig.update_layout(template=CHART_TEMPLATE, height=400)
    st.plotly_chart(fig, width='stretch')


def _render_returns_chart(timeframes: dict[str, PeriodStats | None]) -> None:
    st.markdown("### Period Returns")

    labels = [l for l, s in timeframes.items() if s]
    returns = [s["change_pct"] for s in timeframes.values() if s]  # type: ignore[index]
    colors = ["#28a745" if r >= 0 else "#dc3545" for r in returns]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=returns,
            marker_color=colors,
            text=[f"{r:+.2f}%" for r in returns],
            textposition="auto",
        )
    )
    fig.update_layout(
        title="Returns by Timeframe",
        yaxis_title="Return %",
        template=CHART_TEMPLATE,
        height=400,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig, width='stretch')
