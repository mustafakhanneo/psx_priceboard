"""
config/styles.py
================
All custom CSS injected into the Streamlit app via st.markdown().
Keeping CSS here prevents style strings from cluttering component code.
"""

APP_CSS = """
<style>
    /* ── Typography & layout ──────────────────────────────────────── */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* ── Metric cards ─────────────────────────────────────────────── */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }

    /* ── Colour helpers ───────────────────────────────────────────── */
    .positive { color: #28a745; font-weight: bold; }
    .negative { color: #dc3545; font-weight: bold; }

    /* ── Tabs ─────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"]      { padding: 10px 20px; border-radius: 4px; }

    /* ── Data tables ──────────────────────────────────────────────── */
    .dataframe th { background-color: #f8f9fa; color: #333; font-weight: 600; }
    .dataframe td { text-align: right; }

    /* ── Info / warning boxes ─────────────────────────────────────── */
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
</style>
"""
