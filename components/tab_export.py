"""
components/tab_export.py
========================
"Export Data" tab — JSON report, CSV download, raw data preview.
"""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from utils.analysis import PeriodStats


def render_export_tab(
    df: pd.DataFrame,
    symbol: str,
    current_price: float,
    daily_change: float,
    daily_change_pct: float,
    all_time: PeriodStats,
    timeframes: dict[str, PeriodStats | None],
    moving_averages: dict[str, float],
) -> None:
    """Render the export / download tab."""

    st.markdown("### Export Data & Reports")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### JSON Report")
        report = {
            "symbol":          symbol,
            "current_price":   current_price,
            "daily_change":    daily_change,
            "daily_change_pct": daily_change_pct,
            "all_time_high":   all_time["high"],
            "all_time_low":    all_time["low"],
            "timeframes": {
                k: {
                    "high":       v["high"],
                    "low":        v["low"],
                    "change_pct": v["change_pct"],
                }
                for k, v in timeframes.items()
                if v
            },
            "moving_averages": moving_averages,
        }
        st.download_button(
            label="Download JSON",
            data=json.dumps(report, indent=2, default=str),
            file_name=f"{symbol}_report.json",
            mime="application/json",
        )

    with col2:
        st.markdown("#### CSV Data")
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False),
            file_name=f"{symbol}_data.csv",
            mime="text/csv",
        )

    with col3:
        st.markdown("#### Raw Data Preview")
        st.dataframe(df.tail(10), use_container_width=True)
