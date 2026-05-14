"""
config/settings.py
==================
Central configuration for PSX Tracker.
All constants, defaults, and app-level settings live here.
"""

from datetime import date, timedelta

# ---------------------------------------------------------------------------
# External API endpoints
# ---------------------------------------------------------------------------
PSX_SYMBOLS_URL = "https://dps.psx.com.pk/symbols"

# ---------------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------------
APP_TITLE = "PSX Price Tracker"
APP_ICON = "📈"
APP_SUBTITLE = "Pakistan Stock Exchange — Comprehensive Stock Analysis"

# ---------------------------------------------------------------------------
# Chart / UI defaults
# ---------------------------------------------------------------------------
DEFAULT_MA_PERIODS = [20, 50, 200]
ALL_MA_PERIODS = [5, 10, 20, 50, 100, 200]

MA_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

CANDLESTICK_RISING_COLOR = "#28a745"
CANDLESTICK_FALLING_COLOR = "#dc3545"

CHART_TEMPLATE = "plotly_white"

# ---------------------------------------------------------------------------
# Date defaults
# ---------------------------------------------------------------------------
DEFAULT_START_DATE = date.today() - timedelta(days=3650)   # ~10 years
DEFAULT_END_DATE = date.today()

QUICK_RANGES: dict[str, date | None] = {
    "Custom": None,
    "1 Month":   date.today() - timedelta(days=30),
    "3 Months":  date.today() - timedelta(days=90),
    "6 Months":  date.today() - timedelta(days=180),
    "1 Year":    date.today() - timedelta(days=365),
    "3 Years":   date.today() - timedelta(days=1095),
    "5 Years":   date.today() - timedelta(days=1825),
    "All Time":  date(2015, 1, 1),
}

# ---------------------------------------------------------------------------
# Timeframe analysis windows (label → days)
# ---------------------------------------------------------------------------
TIMEFRAME_WINDOWS: dict[str, int] = {
    "Daily (1D)":       1,
    "3 Days":           3,
    "Weekly (7D)":      7,
    "15 Days":          15,
    "Monthly (30D)":    30,
    "3 Months (90D)":   90,
    "6 Months (180D)":  180,
    "9 Months (270D)":  270,
    "Yearly (365D)":    365,
    "3 Years (1095D)":  1095,
}

# ---------------------------------------------------------------------------
# Fallback ticker list (used when psxdata.tickers() fails)
# ---------------------------------------------------------------------------
FALLBACK_TICKERS: dict[str, str] = {
    "HBL":   "Habib Bank Limited",
    "OGDC":  "Oil & Gas Development Company",
    "ENGRO": "Engro Corporation",
    "LUCK":  "Lucky Cement",
    "MCB":   "MCB Bank Limited",
    "PPL":   "Pakistan Petroleum Limited",
    "UNITY": "Unity Foods",
    "TRG":   "TRG Pakistan",
    "SILK":  "Silk Bank Limited",
    "KEL":   "K-Electric Limited",
    "BAHL":  "Bank AL Habib Limited",
    "BAFL":  "Bank Alfalah Limited",
    "DGKC":  "D.G. Khan Cement",
    "FCCL":  "Fauji Cement",
    "FFBL":  "Fauji Fertilizer Bin Qasim",
    "FFC":   "Fauji Fertilizer Company",
    "HUBC":  "Hub Power Company",
    "INDU":  "Indus Motor Company",
    "KAPCO": "Kot Addu Power Company",
    "LCI":   "Lahore Cement",
    "MARI":  "Mari Petroleum",
    "MLCF":  "Maple Leaf Cement",
    "NBP":   "National Bank of Pakistan",
    "NCPL":  "Nishat Chunian Power",
    "NML":   "Nishat Mills",
    "POL":   "Pakistan Oilfields",
    "PSO":   "Pakistan State Oil",
    "SNGP":  "Sui Northern Gas Pipelines",
    "SSGC":  "Sui Southern Gas Company",
    "UBL":   "United Bank Limited",
}

# Base prices used only when generating sample data
SAMPLE_BASE_PRICES: dict[str, float] = {
    "HBL":   150,
    "OGDC":  80,
    "ENGRO": 200,
    "LUCK":  350,
    "MCB":   120,
    "PPL":   90,
    "UNITY": 25,
    "TRG":   45,
    "SILK":  15,
    "PACE":  10,
    "KEL":   3,
    "PIAA":  5,
}
SAMPLE_DEFAULT_BASE_PRICE = 100
