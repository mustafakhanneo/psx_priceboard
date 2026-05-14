"""
utils/analysis.py
=================
Pure analytical functions — no Streamlit or Plotly imports.
Each function takes a DataFrame and returns plain Python data structures.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TypedDict

import pandas as pd


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

class PeriodStats(TypedDict):
    high: float
    low: float
    high_date: pd.Timestamp
    low_date: pd.Timestamp
    open: float
    close: float
    volume: int
    change_pct: float
    days: int


# ---------------------------------------------------------------------------
# Per-period statistics
# ---------------------------------------------------------------------------

def get_price_stats(df: pd.DataFrame, days: int | None = None) -> PeriodStats | None:
    """
    Calculate OHLCV statistics for the most-recent *days* calendar days.
    If *days* is None, use the entire DataFrame.

    Returns None when the slice is empty.
    """
    if days is not None:
        end_date = df["Date"].max()
        start = end_date - timedelta(days=days)
        df = df[(df["Date"] >= start) & (df["Date"] <= end_date)]

    if len(df) == 0:
        return None

    return PeriodStats(
        high=df["High"].max(),
        low=df["Low"].min(),
        high_date=df.loc[df["High"].idxmax(), "Date"],
        low_date=df.loc[df["Low"].idxmin(), "Date"],
        open=float(df.iloc[0]["Open"]),
        close=float(df.iloc[-1]["Close"]),
        volume=int(df["Volume"].sum()) if "Volume" in df.columns else 0,
        change_pct=(
            (df.iloc[-1]["Close"] - df.iloc[0]["Open"]) / df.iloc[0]["Open"]
        ) * 100,
        days=len(df),
    )


# ---------------------------------------------------------------------------
# Moving averages
# ---------------------------------------------------------------------------

def get_moving_averages(df: pd.DataFrame) -> dict[str, float]:
    """
    Return {f'MA{period}': value} for all periods where sufficient history exists.
    """
    close = df["Close"]
    return {
        f"MA{p}": float(close.rolling(window=p).mean().iloc[-1])
        for p in [5, 10, 20, 50, 100, 200]
        if len(close) >= p
    }


# ---------------------------------------------------------------------------
# Support & Resistance
# ---------------------------------------------------------------------------

def get_support_resistance(df: pd.DataFrame, window: int = 20) -> dict[str, float]:
    """
    Simple support/resistance from the high/low of the last *window* rows.
    """
    recent = df.tail(window)
    return {
        "support":    float(recent["Low"].min()),
        "resistance": float(recent["High"].max()),
    }
