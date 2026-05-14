"""
components/sidebar.py
=====================
Renders the Streamlit sidebar and returns all user-selected options
as a plain dataclass so the main app never has to reach into st.session_state
or sidebar widgets directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import streamlit as st

from config.settings import (
    ALL_MA_PERIODS,
    DEFAULT_END_DATE,
    DEFAULT_MA_PERIODS,
    DEFAULT_START_DATE,
    QUICK_RANGES,
)
from utils.data import TickerInfo, load_tickers


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

@dataclass
class SidebarOptions:
    symbol: str
    start_date: date
    end_date: date
    show_volume: bool
    show_ma: bool
    ma_periods: list[int]
    tickers: dict[str, TickerInfo]


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def render_sidebar() -> SidebarOptions:
    """Draw the sidebar and return the collected options."""

    with st.sidebar:
        st.markdown("## 📈 PSX Tracker")
        st.markdown("---")

        # ── Ticker selection ──────────────────────────────────────────────
        st.markdown("### Select Stock")
        tickers = load_tickers()

        # Optional sector filter
        sectors = sorted({v["sector"] for v in tickers.values() if v["sector"]})
        selected_sector = st.selectbox(
            "Filter by sector",
            ["All Sectors"] + sectors,
        )

        # Optionally hide debt / ETF instruments
        col_a, col_b = st.columns(2)
        with col_a:
            hide_debt = st.checkbox("Hide Debt", value=False)
        with col_b:
            hide_etf = st.checkbox("Hide ETFs", value=False)

        # Apply filters
        filtered = {
            sym: info for sym, info in tickers.items()
            if (selected_sector == "All Sectors" or info["sector"] == selected_sector)
            and not (hide_debt and info["is_debt"])
            and not (hide_etf and info["is_etf"])
        }
        if not filtered:
            st.warning("No tickers match current filters.")
            filtered = tickers  # reset silently

        ticker_search = (
            st.text_input("Search ticker or name", "", placeholder="e.g. HBL, Engro…")
            .strip()
        )

        symbol = _resolve_symbol(ticker_search, filtered)

        # Info card for selected symbol
        if symbol in tickers:
            info = tickers[symbol]
            badges = []
            if info["is_etf"]:
                badges.append("🔷 ETF")
            if info["is_debt"]:
                badges.append("🏦 Debt")
            badge_str = " · ".join(badges) if badges else "🟢 Equity"
            st.info(
                f"**{symbol}** — {info['name']}  \n"
                f"Sector: {info['sector'] or 'N/A'} · {badge_str}"
            )

        st.markdown("---")

        # ── Date range ────────────────────────────────────────────────────
        st.markdown("### Date Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date: date = st.date_input("Start", DEFAULT_START_DATE)
        with col2:
            end_date: date = st.date_input("End", DEFAULT_END_DATE)

        st.markdown("---")

        # ── Quick ranges ──────────────────────────────────────────────────
        st.markdown("### Quick Select")
        quick = st.selectbox("Preset ranges", list(QUICK_RANGES.keys()))
        override = QUICK_RANGES.get(quick)
        if override is not None:
            start_date = override

        st.markdown("---")

        # ── Chart settings ────────────────────────────────────────────────
        st.markdown("### Settings")
        show_volume: bool = st.checkbox("Show Volume", value=True)
        show_ma: bool     = st.checkbox("Show Moving Averages", value=True)
        ma_periods: list[int] = st.multiselect(
            "MA Periods",
            ALL_MA_PERIODS,
            default=DEFAULT_MA_PERIODS,
        )

        st.markdown("---")
        st.caption("Made with ❤️ for PSX Investors")

    return SidebarOptions(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        show_volume=show_volume,
        show_ma=show_ma,
        ma_periods=ma_periods,
        tickers=tickers,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_symbol(search: str, tickers: dict[str, TickerInfo]) -> str:
    """
    Return a ticker symbol given the user's search string.
    Matches against both symbol and company name (case-insensitive).
    Falls back to a selectbox when there is no direct match.
    """
    search_upper = search.upper()

    # Exact symbol match
    if search_upper and search_upper in tickers:
        st.sidebar.success(f"✓ Exact match: {search_upper}")
        return search_upper

    # Partial match on symbol or name
    if search:
        filtered = {
            sym: info for sym, info in tickers.items()
            if search_upper in sym or search.lower() in info["name"].lower()
        }
        if filtered:
            return st.selectbox(
                f"{len(filtered)} match(es)",
                list(filtered.keys()),
                format_func=lambda x: f"{x} — {filtered[x]['name']}",
            )
        st.sidebar.error(f"No ticker found matching '{search}'")

    return st.selectbox(
        "Choose a stock",
        list(tickers.keys()),
        format_func=lambda x: f"{x} — {tickers[x]['name']}",
    )