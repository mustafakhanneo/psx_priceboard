"""
utils/data.py
=============
All data-layer logic:
  - fetch_psx_data()      — live data via psxdata, fallback to sample
  - generate_sample_data() — reproducible OHLCV sample data
  - validate_and_fix_data() — cleaning / OHLC constraint enforcement
  - load_tickers()         — fetch ticker list with fallback
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import date, timedelta

from config.settings import (
    FALLBACK_TICKERS,
    SAMPLE_BASE_PRICES,
    PSX_SYMBOLS_URL,
    SAMPLE_DEFAULT_BASE_PRICE,
)

class TickerInfo(TypedDict):
    name: str
    sector: str
    is_etf: bool
    is_debt: bool
 
 
@st.cache_data(ttl=86_400)   # refresh once per day
def load_tickers() -> dict[str, TickerInfo]:
    """
    Fetch the full PSX symbol list from the official API.
 
    Returns
    -------
    {symbol: TickerInfo}  — always non-empty (falls back to built-ins on error).
 
    API endpoint: GET https://dps.psx.com.pk/symbols
    Response: JSON array of objects with keys:
        symbol, name, sectorName, isETF, isDebt
    """
    try:
        resp = requests.get(PSX_SYMBOLS_URL, timeout=10)
        resp.raise_for_status()
        raw: list[dict] = resp.json()
 
        if not raw:
            raise ValueError("Empty response from PSX symbols API")
 
        result: dict[str, TickerInfo] = {}
        for item in raw:
            sym = str(item.get("symbol", "")).strip().upper()
            if not sym:
                continue
            result[sym] = TickerInfo(
                name=str(item.get("name", sym)).strip(),
                sector=str(item.get("sectorName", "")).strip(),
                is_etf=bool(item.get("isETF", False)),
                is_debt=bool(item.get("isDebt", False)),
            )
 
        st.sidebar.success(f"Loaded {len(result):,} PSX symbols")
        return result
 
    except Exception as exc:
        st.sidebar.warning(
            f"PSX symbols API unavailable ({exc}). Using built-in list."
        )
        # Convert fallback dict[str, str] → dict[str, TickerInfo]
        return {
            sym: TickerInfo(name=name, sector="", is_etf=False, is_debt=False)
            for sym, name in FALLBACK_TICKERS.items()
        }
 

# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def fetch_current_price(symbol: str) -> float | None:
    """
    Fetch live price for *symbol* via psxdata.quote().
    Returns QuoteData with just the current price, or None on failure.
    """
    try:
        import psxdata
        raw = psxdata.quote(symbol)
        if isinstance(raw, pd.DataFrame):
            if raw.empty:
                return None
            price = float(raw.iloc[0]["price"])
        elif isinstance(raw, pd.Series):
            price = float(raw["price"])
        elif isinstance(raw, dict):
            price = float(raw["price"])
        else:
            return None
        return price
    except Exception:
        return None

@st.cache_data(ttl=3600)
def fetch_psx_data(
    symbol: str,
    start_date: date,
    end_date: date,
) -> tuple[pd.DataFrame, str]:
    """
    Fetch OHLCV data for *symbol* between *start_date* and *end_date*.

    Returns
    -------
    (df, source)  where source is "psxdata" or "sample".
    """
    try:
        import psxdata

        df: pd.DataFrame = psxdata.stocks(
            symbol, start=str(start_date), end=str(end_date)
        )
        if df is not None and len(df) > 0:
            df = df.reset_index()
            df.columns = [c.strip().title() for c in df.columns]

            # Normalise date column name
            if "Date" not in df.columns:
                date_cols = [c for c in df.columns if "date" in c.lower()]
                if date_cols:
                    df.rename(columns={date_cols[0]: "Date"}, inplace=True)

            return df, "psxdata"

    except Exception as exc:
        st.warning(f"psxdata not available: {exc}")

    return generate_sample_data(symbol, start_date, end_date), "sample"


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

def generate_sample_data(
    symbol: str,
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """
    Generate realistic but synthetic OHLCV data for *symbol*.
    Seed is derived from the symbol so results are reproducible.
    """
    np.random.seed(hash(symbol) % 10_000)

    date_range = pd.date_range(start=start_date, end=end_date, freq="B")
    n = len(date_range)
    base = SAMPLE_BASE_PRICES.get(symbol, SAMPLE_DEFAULT_BASE_PRICE)

    returns = np.random.normal(0.0003, 0.015, n)
    prices = base * np.exp(np.cumsum(returns))

    df = pd.DataFrame(
        {
            "Date":   date_range,
            "Open":   prices * (1 + np.random.normal(0, 0.005, n)),
            "High":   prices * (1 + np.abs(np.random.normal(0, 0.01, n))),
            "Low":    prices * (1 - np.abs(np.random.normal(0, 0.01, n))),
            "Close":  prices,
            "Volume": np.random.randint(100_000, 5_000_000, n),
        }
    )

    # Enforce OHLC constraints row-by-row
    df["High"] = df[["High", "Open", "Close"]].max(axis=1)
    df["Low"]  = df[["Low",  "Open", "Close"]].min(axis=1)

    return df


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_and_fix_data(df: pd.DataFrame | None) -> pd.DataFrame | None:
    """
    Clean and normalise a raw OHLCV DataFrame:
      - parse Date to datetime
      - sort chronologically
      - drop duplicate dates (keep first)
      - coerce numeric columns
      - re-enforce OHLC constraints
    """
    if df is None or len(df) == 0:
        return df

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = (
        df.sort_values("Date")
          .drop_duplicates(subset=["Date"], keep="first")
          .reset_index(drop=True)
    )

    for col in ("Open", "High", "Low", "Close"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Volume" in df.columns:
        df["Volume"] = (
            pd.to_numeric(df["Volume"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    # Re-enforce OHLC constraints (vectorised)
    df["High"] = df[["High", "Open", "Close"]].max(axis=1)
    df["Low"]  = df[["Low",  "Open", "Close"]].min(axis=1)

    return df
