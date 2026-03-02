"""
PPC Spend Projector — v2.0
Six models · Shared persistent data · Daily entry
"""

import calendar
import json
from datetime import date, timedelta
from io import BytesIO

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="PPC Spend Projector",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Fonts ──────────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif !important; }

/* ── App background ──────────────────────────────────────────────────────────── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section[data-testid="stMain"] > div {
    background-color: #f1f5f9 !important;
    color: #1f2937 !important;
}
.main .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }

/* ── Sidebar ────────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(175deg, #1e1b4b 0%, #312e81 60%, #3730a3 100%) !important;
    border-right: 1px solid #4338ca !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span:not([class*="hidden"]) {
    color: #c7d2fe !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: #ffffff !important;
    letter-spacing: -0.01em;
}
[data-testid="stSidebar"] hr { border-color: #4338ca !important; margin: 0.6rem 0; }
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px dashed #6366f1 !important;
    border-radius: 8px;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] *,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] * {
    color: #a5b4fc !important;
}
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"] {
    color: #a5b4fc !important;
}

/* ── BUTTONS ─────────────────────────────────────────────────────────────────── */
button[kind="secondary"],
button[kind="primary"],
.stButton button,
div[data-testid="stButton"] button,
div[data-testid="stBaseButton-secondary"] button,
div[data-testid="stBaseButton-primary"] button {
    background-color: #4f46e5 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    transition: background-color 0.15s ease, box-shadow 0.15s ease !important;
    box-shadow: 0 1px 4px rgba(79, 70, 229, 0.3) !important;
}
.stButton button p, .stButton button span,
div[data-testid="stButton"] button p, div[data-testid="stButton"] button span,
div[data-testid="stBaseButton-secondary"] button p, div[data-testid="stBaseButton-secondary"] button span,
div[data-testid="stBaseButton-primary"] button p, div[data-testid="stBaseButton-primary"] button span {
    color: #ffffff !important;
}
button[kind="secondary"]:hover, button[kind="primary"]:hover,
.stButton button:hover,
div[data-testid="stButton"] button:hover,
div[data-testid="stBaseButton-secondary"] button:hover,
div[data-testid="stBaseButton-primary"] button:hover {
    background-color: #4338ca !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4) !important;
}
button[kind="secondary"]:active, button[kind="primary"]:active,
.stButton button:active, div[data-testid="stButton"] button:active {
    background-color: #3730a3 !important;
    color: #ffffff !important;
    box-shadow: none !important;
}

/* ── Sidebar buttons ────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] .stButton button,
[data-testid="stSidebar"] div[data-testid="stButton"] button,
[data-testid="stSidebar"] div[data-testid="stBaseButton-secondary"] button {
    background-color: rgba(99, 102, 241, 0.22) !important;
    color: #c7d2fe !important;
    border: 1px solid rgba(129, 140, 248, 0.35) !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton button p,
[data-testid="stSidebar"] .stButton button span,
[data-testid="stSidebar"] div[data-testid="stButton"] button p,
[data-testid="stSidebar"] div[data-testid="stButton"] button span { color: #c7d2fe !important; }
[data-testid="stSidebar"] .stButton button:hover,
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover,
[data-testid="stSidebar"] div[data-testid="stBaseButton-secondary"] button:hover {
    background-color: rgba(99, 102, 241, 0.42) !important;
    color: #ffffff !important;
    border-color: rgba(129, 140, 248, 0.65) !important;
}
[data-testid="stSidebar"] .stButton button:hover p,
[data-testid="stSidebar"] .stButton button:hover span,
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover p,
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover span { color: #ffffff !important; }

/* ── Danger button ───────────────────────────────────────────────────────────── */
.danger-btn .stButton button, .danger-btn div[data-testid="stButton"] button {
    background-color: rgba(220, 38, 38, 0.1) !important;
    color: #fca5a5 !important;
    border: 1px solid rgba(220, 38, 38, 0.25) !important;
    box-shadow: none !important;
}
.danger-btn .stButton button p, .danger-btn .stButton button span,
.danger-btn div[data-testid="stButton"] button p, .danger-btn div[data-testid="stButton"] button span {
    color: #fca5a5 !important;
}
.danger-btn .stButton button:hover, .danger-btn div[data-testid="stButton"] button:hover {
    background-color: rgba(220, 38, 38, 0.28) !important;
    color: #ffffff !important;
    border-color: rgba(220, 38, 38, 0.55) !important;
}
.danger-btn .stButton button:hover p, .danger-btn .stButton button:hover span,
.danger-btn div[data-testid="stButton"] button:hover p, .danger-btn div[data-testid="stButton"] button:hover span {
    color: #ffffff !important;
}

/* ── Metric cards ────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background-color: #ffffff !important;
    border: 1px solid #e0e7ff !important;
    border-left: 5px solid #4f46e5 !important;
    border-radius: 12px !important;
    padding: 1.25rem 1.5rem 1rem !important;
    box-shadow: 0 4px 16px rgba(79, 70, 229, 0.07) !important;
}
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p, [data-testid="stMetricLabel"] span,
[data-testid="stMetricLabel"] div, [data-testid="stMetricLabel"] label {
    color: #6366f1 !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] p, [data-testid="stMetricValue"] span,
[data-testid="stMetricValue"] div {
    color: #1f2937 !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

/* ── Dashboard hero header ───────────────────────────────────────────────────── */
.dash-header {
    background: linear-gradient(135deg, #1e1b4b 0%, #3730a3 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 6px 28px rgba(55, 48, 163, 0.25);
}
.dash-month {
    font-size: 1.5rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.02em;
}
.dash-mtd-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #a5b4fc;
    margin-top: 0.75rem;
}
.dash-mtd-value {
    font-size: 2.4rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-top: 0.1rem;
}
.dash-right { text-align: right; }
.dash-day-label {
    font-size: 0.78rem;
    color: #c7d2fe;
    margin-bottom: 0.55rem;
}
.dash-progress-wrap {
    width: 220px;
    height: 8px;
    background: rgba(255,255,255,0.15);
    border-radius: 99px;
    overflow: hidden;
    margin-left: auto;
}
.dash-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #818cf8, #c7d2fe);
    border-radius: 99px;
}

/* ── Model card (2-column grid) ──────────────────────────────────────────────── */
.model-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.2rem 1.4rem 0.95rem;
    margin-bottom: 0.35rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    transition: box-shadow 0.18s ease, border-color 0.18s ease;
    min-height: 115px;
}
.model-card:hover {
    box-shadow: 0 6px 22px rgba(79,70,229,0.13);
    border-color: #c7d2fe;
}
.mc-header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 0.3rem;
}
.mc-name {
    font-weight: 700;
    color: #1e1b4b;
    font-size: 0.9rem;
}
.mc-total {
    font-size: 1.85rem;
    font-weight: 800;
    color: #4f46e5;
    letter-spacing: -0.025em;
    line-height: 1.05;
    margin-bottom: 0.3rem;
}
.mc-desc {
    font-size: 0.7rem;
    color: #9ca3af;
    line-height: 1.4;
}
.model-default-badge {
    display: inline-block;
    background: #ede9fe;
    color: #5b21b6;
    font-size: 0.6rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 2px 7px;
    border-radius: 99px;
    vertical-align: middle;
}

/* ── Main text ───────────────────────────────────────────────────────────────── */
.main h1, .main h2, .main h3, .main h4,
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3 {
    color: #1e1b4b !important;
}
[data-testid="stMain"] p,
[data-testid="stMain"] label,
[data-testid="stMain"] li {
    color: #374151 !important;
}

/* ── Expander ────────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    font-weight: 600 !important;
    color: #334155 !important;
    font-size: 0.92rem;
}

/* ── Divider ─────────────────────────────────────────────────────────────────── */
hr { border-color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
DOW_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

MODELS = {
    "dod_chain":    "DoD Chain",
    "adaptive_dow": "Adaptive DoW ★",
    "same_dow":     "Same-DoW Avg",
    "ema_baseline": "EMA Baseline",
    "trend_dow":    "Trend-Adj DoW",
    "ensemble":     "Ensemble",
}

DEFAULT_MODEL_PARAMS: dict = {
    "dod_chain":    {"lookback_weeks": 8,  "use_trimmed_mean": True},
    "adaptive_dow": {"lookback_weeks": 8},
    "same_dow":     {"lookback_weeks": 8},
    "ema_baseline": {"ema_span": 14, "use_ewma": True, "ewma_halflife": 4},
    "trend_dow":    {"lookback_weeks": 8,  "trend_lookback_weeks": 4},
    "ensemble":     {},
}

MODEL_DESCRIPTIONS = {
    "dod_chain":    "Chains day-over-day historical ratios from the last actual spend. Re-anchors automatically as you enter each day.",
    "adaptive_dow": "Per-weekday averages scaled by how this week is performing vs history.",
    "same_dow":     "Simple average spend for each day of the week over the lookback window.",
    "ema_baseline": "Exponential moving average of total spend, distributed by weekday pattern.",
    "trend_dow":    "Detects a growth/decline trend and applies it to weekday averages.",
    "ensemble":     "Median of all five other models — reduces the impact of any single model being wrong.",
}

# ══════════════════════════════════════════════════════════════════════════════
# APPS SCRIPT DATA LAYER
# ══════════════════════════════════════════════════════════════════════════════

def _as_configured() -> bool:
    return bool(st.secrets.get("AS_URL", "")) and bool(st.secrets.get("AS_SECRET", ""))


def _as_get(action: str) -> dict:
    r = requests.get(
        st.secrets.get("AS_URL", ""),
        params={"action": action, "secret": st.secrets.get("AS_SECRET", "")},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def _as_post(action: str, **kwargs) -> None:
    payload = {"action": action, "secret": st.secrets.get("AS_SECRET", ""), **kwargs}
    try:
        r = requests.post(st.secrets.get("AS_URL", ""), json=payload, timeout=30)
    except requests.exceptions.Timeout:
        raise RuntimeError("Apps Script timed out. Try again in a moment.")
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(f"Could not reach Apps Script: {exc}")
    if not r.ok:
        snippet = r.text[:300] if r.text else "(empty response)"
        raise RuntimeError(
            f"Apps Script returned HTTP {r.status_code}. Response: {snippet}"
        )
    try:
        body = r.json()
        if isinstance(body, dict) and body.get("error"):
            raise RuntimeError(f"Apps Script error: {body['error']}")
    except (ValueError, KeyError):
        pass


@st.cache_data(ttl=30)
def load_spend_history() -> dict:
    """Returns {date_str: float}. Cached 30 s."""
    if not _as_configured():
        return {}
    try:
        return _as_get("get_history")
    except Exception:
        return {}


@st.cache_data(ttl=30)
def load_model_settings() -> dict:
    """Returns {model_key: params_dict}. Cached 30 s."""
    if not _as_configured():
        return {}
    try:
        return _as_get("get_settings")
    except Exception:
        return {}


def save_spend_entry(date_str: str, amount: float) -> None:
    _as_post("save_entry", date=date_str, amount=round(float(amount), 2))
    st.cache_data.clear()


def save_model_settings(model_key: str, params: dict) -> None:
    current = _as_get("get_settings")
    current[model_key] = params
    _as_post("save_settings", settings=current)
    st.cache_data.clear()


def bulk_save_history(entries: dict) -> None:
    """Merge new entries into existing history."""
    _as_post("bulk_save", entries={k: round(float(v), 2) for k, v in entries.items()})
    st.cache_data.clear()


def clear_all_data() -> None:
    _as_post("clear_all")
    st.cache_data.clear()


# ══════════════════════════════════════════════════════════════════════════════
# DATA PREPARATION
# ══════════════════════════════════════════════════════════════════════════════

def history_to_df(history: dict) -> pd.DataFrame:
    """Convert {date_str: amount} → sorted DataFrame with 'date', 'spend', 'dow' columns."""
    if not history:
        return pd.DataFrame(columns=["date", "spend", "dow"])
    rows = []
    for k, v in history.items():
        try:
            rows.append({"date": pd.to_datetime(k), "spend": float(v)})
        except (ValueError, TypeError):
            continue
    if not rows:
        return pd.DataFrame(columns=["date", "spend", "dow"])
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    df["dow"] = df["date"].dt.strftime("%a")
    return df


def parse_upload(file) -> dict:
    """Parse CSV or Excel upload → {date_str: float}. Flexible column detection."""
    name = file.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    date_col = None
    spend_col = None
    for col in df.columns:
        cl = col.lower().strip()
        if date_col is None and any(k in cl for k in ("date", "day")):
            date_col = col
        if spend_col is None and any(k in cl for k in ("spend", "cost", "amount", "revenue")):
            spend_col = col

    if date_col is None:
        date_col = df.columns[0]
    if spend_col is None:
        spend_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, spend_col])

    result: dict = {}
    for _, row in df.iterrows():
        d = row[date_col].strftime("%Y-%m-%d")
        try:
            val = float(str(row[spend_col]).replace(",", "").replace("$", "").strip())
            result[d] = val
        except (ValueError, TypeError):
            continue
    return result


# ══════════════════════════════════════════════════════════════════════════════
# MATH — HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _same_dow_avg(df: pd.DataFrame, lookback_weeks) -> dict:
    """Mean spend per short-name weekday (Mon…Sun) over lookback window."""
    if lookback_weeks:
        cutoff = df["date"].max() - pd.Timedelta(weeks=int(lookback_weeks))
        sub = df[df["date"] >= cutoff]
    else:
        sub = df
    avgs = sub.groupby("dow")["spend"].mean().to_dict()
    # Fill any missing weekdays with overall mean
    overall = sub["spend"].mean() if not sub.empty else 0.0
    return {d: avgs.get(d, overall) for d in DOW_SHORT}


def _week_scale_factor(df: pd.DataFrame, dow_avg: dict) -> float:
    """Scale factor from this week's actuals vs DoW averages. Capped [0.5, 2.0]."""
    today_ts = pd.Timestamp.today().normalize()
    week_start = today_ts - pd.Timedelta(days=today_ts.dayofweek)
    this_week = df[df["date"] >= week_start]
    if this_week.empty:
        return 1.0
    ratios = []
    for _, row in this_week.iterrows():
        avg = dow_avg.get(row["dow"], 0.0)
        if avg > 0:
            ratios.append(row["spend"] / avg)
    return float(np.clip(np.median(ratios), 0.5, 2.0)) if ratios else 1.0


def _dow_multipliers_equal(dow_avg: dict) -> dict:
    total = sum(dow_avg.get(d, 0.0) for d in DOW_SHORT)
    if total == 0:
        return {d: 1 / 7 for d in DOW_SHORT}
    return {d: dow_avg.get(d, 0.0) / total for d in DOW_SHORT}


def _dow_multipliers_ewma(df: pd.DataFrame, halflife_weeks: int) -> dict:
    """EWMA-weighted DoW multipliers. halflife in weeks → converted to days."""
    df2 = df.sort_values("date").copy()
    hl_days = halflife_weeks * 7
    n = len(df2)
    weights = np.exp(-np.log(2) / hl_days * (n - 1 - np.arange(n)))
    df2["_w"] = weights
    grouped = df2.groupby("dow").apply(
        lambda g: (g["spend"] * g["_w"]).sum() / g["_w"].sum()
    )
    total = sum(grouped.get(d, 0.0) for d in DOW_SHORT)
    if total == 0:
        return {d: 1 / 7 for d in DOW_SHORT}
    return {d: grouped.get(d, 0.0) / total for d in DOW_SHORT}


def _month_calendar(year: int, month: int, today: date) -> tuple[list[date], dict]:
    """Return (all_days_in_month, actual_dict). actual_dict: date → spend."""
    days_in_month = calendar.monthrange(year, month)[1]
    all_days = [date(year, month, d) for d in range(1, days_in_month + 1)]
    return all_days, {}


# ══════════════════════════════════════════════════════════════════════════════
# MATH — MODEL PROJECTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _actual_dict(df: pd.DataFrame, year: int, month: int) -> dict:
    """Dict of date → spend for actuals in given month."""
    sub = df[(df["date"].dt.year == year) & (df["date"].dt.month == month)]
    return {row["date"].date(): row["spend"] for _, row in sub.iterrows()}


def _build_proj_df(all_days: list, actual: dict, today: date, projected_values: dict) -> pd.DataFrame:
    """Assemble result DataFrame from actual + projected dicts."""
    rows = []
    for d in all_days:
        if d in actual:
            rows.append({"date": pd.Timestamp(d), "spend": actual[d], "type": "actual"})
        elif d < today:
            rows.append({"date": pd.Timestamp(d), "spend": None, "type": "missing"})
        else:
            rows.append({"date": pd.Timestamp(d), "spend": projected_values.get(d, 0.0), "type": "projected"})
    return pd.DataFrame(rows)


def project_dod_chain(df: pd.DataFrame, params: dict, today: date) -> pd.DataFrame:
    lookback = params.get("lookback_weeks")
    trimmed  = params.get("use_trimmed_mean", True)

    hist = df.sort_values("date").copy()
    if lookback:
        cutoff = pd.Timestamp(today) - pd.Timedelta(weeks=int(lookback))
        hist = hist[hist["date"] >= cutoff]

    # Build day-over-day ratio pairs per (prev_dow, curr_dow) transition
    pairs: dict = {}
    for i in range(1, len(hist)):
        prev = hist.iloc[i - 1]
        curr = hist.iloc[i]
        gap = (curr["date"] - prev["date"]).days
        if gap != 1 or prev["spend"] <= 0:
            continue
        key = (prev["dow"], curr["dow"])
        pairs.setdefault(key, []).append(curr["spend"] / prev["spend"])

    ratios: dict = {}
    for key, vals in pairs.items():
        if len(vals) >= 3 and trimmed:
            ratios[key] = float(np.mean(sorted(vals)[1:-1]))
        else:
            ratios[key] = float(np.mean(vals))

    year, month = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    all_days = [date(year, month, d) for d in range(1, days_in_month + 1)]
    actual = _actual_dict(df, year, month)

    # Fallback DoW avg for days with no chain anchor
    dow_avg = _same_dow_avg(df, lookback)

    projected: dict = {}
    last_val = None
    last_dow = None

    # Prime anchor: last actual in full history before current month.
    # Skip stale anchors (> 60 days before month start) to avoid compounding errors
    # when data has large gaps — fall back to DoW averages instead.
    prior = df[df["date"] < pd.Timestamp(date(year, month, 1))].sort_values("date")
    if not prior.empty:
        anchor_date = prior.iloc[-1]["date"]
        month_start = pd.Timestamp(date(year, month, 1))
        if (month_start - anchor_date).days <= 60:
            last_val = prior.iloc[-1]["spend"]
            last_dow = prior.iloc[-1]["dow"]

    for d in all_days:
        dow = d.strftime("%a")
        if d in actual:
            last_val = actual[d]
            last_dow = dow
        elif d >= today:
            if last_val is not None and last_dow is not None:
                key = (last_dow, dow)
                ratio = ratios.get(key, 1.0)
                val = last_val * ratio
            else:
                val = dow_avg.get(dow, 0.0)
            projected[d] = max(0.0, val)
            last_val = projected[d]
            last_dow = dow

    return _build_proj_df(all_days, actual, today, projected)


def project_adaptive_dow(df: pd.DataFrame, params: dict, today: date) -> pd.DataFrame:
    lookback = params.get("lookback_weeks", 8)
    dow_avg  = _same_dow_avg(df, lookback)
    scale    = _week_scale_factor(df, dow_avg)

    year, month = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    all_days = [date(year, month, d) for d in range(1, days_in_month + 1)]
    actual = _actual_dict(df, year, month)

    projected = {d: max(0.0, dow_avg.get(d.strftime("%a"), 0.0) * scale)
                 for d in all_days if d >= today and d not in actual}
    return _build_proj_df(all_days, actual, today, projected)


def project_same_dow(df: pd.DataFrame, params: dict, today: date) -> pd.DataFrame:
    lookback = params.get("lookback_weeks", 8)
    dow_avg  = _same_dow_avg(df, lookback)

    year, month = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    all_days = [date(year, month, d) for d in range(1, days_in_month + 1)]
    actual = _actual_dict(df, year, month)

    projected = {d: max(0.0, dow_avg.get(d.strftime("%a"), 0.0))
                 for d in all_days if d >= today and d not in actual}
    return _build_proj_df(all_days, actual, today, projected)


def project_ema_baseline(df: pd.DataFrame, params: dict, today: date) -> pd.DataFrame:
    use_ewma  = params.get("use_ewma", True)
    ema_span  = params.get("ema_span", 14)
    halflife  = params.get("ewma_halflife", 4)

    hist = df.sort_values("date").copy()
    ema_val = float(hist["spend"].ewm(span=ema_span).mean().iloc[-1])

    if use_ewma:
        mults = _dow_multipliers_ewma(df, halflife)
    else:
        dow_avg = _same_dow_avg(df, None)
        mults   = _dow_multipliers_equal(dow_avg)

    year, month = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    all_days = [date(year, month, d) for d in range(1, days_in_month + 1)]
    actual = _actual_dict(df, year, month)

    total_weight = sum(mults[d.strftime("%a")] for d in all_days)
    projected = {}
    for d in all_days:
        if d >= today and d not in actual:
            m = mults[d.strftime("%a")]
            projected[d] = max(0.0, ema_val * m * days_in_month / total_weight) if total_weight > 0 else 0.0

    return _build_proj_df(all_days, actual, today, projected)


def project_trend_dow(df: pd.DataFrame, params: dict, today: date) -> pd.DataFrame:
    lookback       = params.get("lookback_weeks", 8)
    trend_lookback = params.get("trend_lookback_weeks", 4)
    dow_avg        = _same_dow_avg(df, lookback)

    # OLS slope on recent spend
    hist = df.sort_values("date").copy()
    trend_cutoff = hist["date"].max() - pd.Timedelta(weeks=int(trend_lookback) * 2)
    trend_data   = hist[hist["date"] >= trend_cutoff].copy()

    slope = 0.0
    days_since_midpoint = 0
    if len(trend_data) >= 3:
        x = (trend_data["date"] - trend_data["date"].min()).dt.days.values.astype(float)
        y = trend_data["spend"].values.astype(float)
        slope = float(np.polyfit(x, y, 1)[0])
        midpoint_date = trend_data["date"].iloc[len(trend_data) // 2]
        days_since_midpoint = (pd.Timestamp(today) - midpoint_date).days

    year, month = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    all_days = [date(year, month, d) for d in range(1, days_in_month + 1)]
    actual = _actual_dict(df, year, month)

    projected = {}
    for d in all_days:
        if d >= today and d not in actual:
            days_out = (d - today).days
            base = dow_avg.get(d.strftime("%a"), 0.0)
            projected[d] = max(0.0, base + slope * (days_since_midpoint + days_out))

    return _build_proj_df(all_days, actual, today, projected)


def run_all_models(df: pd.DataFrame, saved_settings: dict, local_overrides: dict, today: date) -> dict:
    """Run all 6 models. Returns {model_key: DataFrame}."""

    def get_params(key: str) -> dict:
        p = dict(DEFAULT_MODEL_PARAMS.get(key, {}))
        p.update(saved_settings.get(key, {}))
        p.update(local_overrides.get(key, {}))
        return p

    proj_fns = {
        "dod_chain":    project_dod_chain,
        "adaptive_dow": project_adaptive_dow,
        "same_dow":     project_same_dow,
        "ema_baseline": project_ema_baseline,
        "trend_dow":    project_trend_dow,
    }

    results: dict = {}
    for key, fn in proj_fns.items():
        results[key] = fn(df, get_params(key), today)

    # Ensemble: median of all 5 models' projected values per day
    year, month = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    all_days = [date(year, month, d) for d in range(1, days_in_month + 1)]
    actual = _actual_dict(df, year, month)

    ens_rows = []
    for d in all_days:
        if d in actual:
            ens_rows.append({"date": pd.Timestamp(d), "spend": actual[d], "type": "actual"})
        elif d < today:
            ens_rows.append({"date": pd.Timestamp(d), "spend": None, "type": "missing"})
        else:
            vals = []
            for key in proj_fns:
                sub = results[key]
                row = sub[sub["date"] == pd.Timestamp(d)]
                if not row.empty and row.iloc[0]["type"] == "projected":
                    v = row.iloc[0]["spend"]
                    if v is not None:
                        vals.append(v)
            med = float(np.median(vals)) if vals else 0.0
            ens_rows.append({"date": pd.Timestamp(d), "spend": med, "type": "projected"})

    results["ensemble"] = pd.DataFrame(ens_rows)
    return results


def projected_total(proj_df: pd.DataFrame, actual_mtd: float) -> float:
    fut = proj_df[proj_df["type"] == "projected"]["spend"]
    return actual_mtd + float(fut.sum())


# ══════════════════════════════════════════════════════════════════════════════
# CHART
# ══════════════════════════════════════════════════════════════════════════════

def make_chart(proj_df: pd.DataFrame, model_name: str) -> go.Figure:
    actual    = proj_df[proj_df["type"] == "actual"]
    future    = proj_df[proj_df["type"] == "projected"]

    fig = go.Figure()

    if not actual.empty:
        fig.add_trace(go.Scatter(
            x=actual["date"], y=actual["spend"],
            mode="lines+markers", name="Actual",
            line=dict(color="#6366f1", width=2.5),
            marker=dict(size=6, color="#6366f1"),
        ))

    if not future.empty:
        # Dashed bridge from last actual to first projected
        if not actual.empty:
            fig.add_trace(go.Scatter(
                x=[actual["date"].iloc[-1], future["date"].iloc[0]],
                y=[actual["spend"].iloc[-1], future["spend"].iloc[0]],
                mode="lines",
                line=dict(color="#a5b4fc", width=2, dash="dot"),
                showlegend=False,
            ))
        fig.add_trace(go.Scatter(
            x=future["date"], y=future["spend"],
            mode="lines+markers", name="Projected",
            line=dict(color="#a5b4fc", width=2, dash="dot"),
            marker=dict(size=5, symbol="circle-open", color="#6366f1"),
        ))

    fig.update_layout(
        title=dict(text=model_name, font=dict(size=15, color="#1e1b4b")),
        xaxis_title=None,
        yaxis_title="Daily Spend ($)",
        hovermode="x unified",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=50, b=10),
        yaxis=dict(tickprefix="$", tickformat=",.0f", gridcolor="#f1f5f9", zerolinecolor="#e2e8f0"),
        xaxis=dict(gridcolor="#f1f5f9"),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# PASSWORD GATE
# ══════════════════════════════════════════════════════════════════════════════
_app_pw = st.secrets.get("APP_PASSWORD", "")
if _app_pw:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.markdown("## 🔒 PPC Spend Projector")
        _entered = st.text_input("Enter password", type="password", key="pw_input")
        if st.button("Unlock"):
            if _entered == _app_pw:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None      # None = dashboard
if "local_params" not in st.session_state:
    st.session_state.local_params: dict = {}    # {model_key: {param: val}}
if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False
if "uploader_counter" not in st.session_state:
    st.session_state.uploader_counter = 0


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOAD
# ══════════════════════════════════════════════════════════════════════════════
history       = load_spend_history()
model_settings = load_model_settings()
df             = history_to_df(history)
today          = date.today()

has_data = len(df) >= 7    # Need at least a week for any model to be meaningful

# Pre-compute projections and totals if we have data
if has_data:
    all_proj  = run_all_models(df, model_settings, st.session_state.local_params, today)
    year, month = today.year, today.month
    actual_mtd  = float(df[(df["date"].dt.year == year) & (df["date"].dt.month == month)]["spend"].sum())
    model_totals = {k: projected_total(all_proj[k], actual_mtd) for k in MODELS}


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📊 PPC Spend Projector")
    if has_data:
        last_row = df.sort_values("date").iloc[-1]
        st.caption(f"Last entry: {last_row['date'].strftime('%b %d, %Y')} · ${last_row['spend']:,.0f}")
    st.markdown("---")

    # ── Daily spend entry ──────────────────────────────────────────────────────
    st.markdown("### 📅 Enter Spend")
    entry_date   = st.date_input("Date", value=today - timedelta(days=1), max_value=today)
    entry_amount = st.number_input("Amount ($)", min_value=0.0, step=100.0, format="%.2f",
                                   key="entry_amount")
    if st.button("💾 Save", use_container_width=True, key="btn_save_spend"):
        if entry_amount > 0:
            if _as_configured():
                try:
                    save_spend_entry(entry_date.strftime("%Y-%m-%d"), entry_amount)
                    st.success(f"Saved ${entry_amount:,.2f} for {entry_date}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Save failed: {exc}")
            else:
                st.warning("Apps Script not configured — see Setup Required below.")
        else:
            st.warning("Enter an amount greater than $0.")

    st.markdown("---")

    # ── Historical upload ──────────────────────────────────────────────────────
    with st.expander("📁 Historical Upload", expanded=False):
        st.caption("Upload a CSV or Excel file with Date and Spend columns. New data is merged with existing.")
        up_file = st.file_uploader(
            "Choose file",
            type=["csv", "xlsx", "xls"],
            key=f"uploader_{st.session_state.uploader_counter}",
        )
        if up_file is not None:
            if st.button("Import & Merge", use_container_width=True, key="btn_import"):
                try:
                    new_entries = parse_upload(up_file)
                    if new_entries:
                        if _as_configured():
                            bulk_save_history(new_entries)
                            st.session_state.uploader_counter += 1
                            st.success(f"Imported {len(new_entries)} records.")
                            st.rerun()
                        else:
                            st.warning("Apps Script not configured — see Setup Required below.")
                    else:
                        st.error("No valid date/spend data found in file.")
                except Exception as exc:
                    st.error(f"Import failed: {exc}")

        st.markdown("---")
        st.markdown("**⚠ Danger Zone**")
        if not st.session_state.confirm_clear:
            st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
            if st.button("🗑 Clear All Data", use_container_width=True, key="btn_clear_start"):
                st.session_state.confirm_clear = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("This will permanently delete all spend history and model settings.")
            confirm_text = st.text_input("Type CLEAR to confirm", key="confirm_input")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Confirm", use_container_width=True, key="btn_clear_confirm"):
                    if confirm_text.strip() == "CLEAR":
                        if _as_configured():
                            try:
                                clear_all_data()
                                st.session_state.confirm_clear = False
                                st.success("All data cleared.")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Clear failed: {exc}")
                                st.session_state.confirm_clear = False
                        else:
                            st.session_state.confirm_clear = False
                            st.info("No backend configured — nothing to clear.")
                            st.rerun()
                    else:
                        st.error("Type CLEAR exactly.")
            with c2:
                if st.button("Cancel", use_container_width=True, key="btn_clear_cancel"):
                    st.session_state.confirm_clear = False
                    st.rerun()

    # ── Setup note if Apps Script not configured ───────────────────────────────
    if not _as_configured():
        st.markdown("---")
        with st.expander("⚙ Setup Required", expanded=True):
            st.markdown("""
Data persistence requires two values in **App Settings → Secrets**:

```toml
AS_URL    = "https://script.google.com/macros/s/.../exec"
AS_SECRET = "your-chosen-api-secret"
```

**Setup (~10 min):**
1. Create a Google Sheet with tabs `Spend History` and `Model Settings`
2. Extensions → Apps Script → paste the provided script → change `SECRET` → Save
3. Deploy → New deployment → Web app → Execute as Me, Anyone → copy URL
4. Add `AS_URL` + `AS_SECRET` to Streamlit secrets above
""")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — DASHBOARD VIEW
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.selected_model is None:

    month_label = today.strftime("%B %Y")

    if not has_data:
        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;
            padding:2.5rem 2rem;text-align:center;
            box-shadow:0 2px 8px rgba(0,0,0,0.04);margin-bottom:1rem">
  <div style="font-size:2.5rem;margin-bottom:0.5rem">📊</div>
  <div style="font-size:1.2rem;font-weight:700;color:#1e1b4b;margin-bottom:0.4rem">{month_label}</div>
  <div style="font-size:0.875rem;color:#6b7280;line-height:1.6">
    Upload historical data via <strong>Historical Upload</strong> in the sidebar,<br>
    or enter a day's spend to get started.
  </div>
</div>""", unsafe_allow_html=True)
    else:
        days_total = calendar.monthrange(year, month)[1]
        pct = min(100, int(today.day / days_total * 100))

        # ── Hero header ───────────────────────────────────────────────────────
        st.markdown(f"""
<div class="dash-header">
  <div>
    <div class="dash-month">{month_label}</div>
    <div class="dash-mtd-label">MTD Actual</div>
    <div class="dash-mtd-value">${actual_mtd:,.0f}</div>
  </div>
  <div class="dash-right">
    <div class="dash-day-label">Day {today.day} of {days_total} &nbsp;·&nbsp; {pct}% through the month</div>
    <div class="dash-progress-wrap">
      <div class="dash-progress-fill" style="width:{pct}%"></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        st.markdown("### Model Comparison — Projected Month Total")

        # ── 2-column card grid ────────────────────────────────────────────────
        model_list = list(MODELS.items())
        for row_start in range(0, len(model_list), 2):
            c1, c2 = st.columns(2, gap="medium")
            for col, idx in [(c1, row_start), (c2, row_start + 1)]:
                if idx >= len(model_list):
                    continue
                key, label = model_list[idx]
                total = model_totals.get(key, 0.0)
                badge = '<span class="model-default-badge">Default</span>' if key == "dod_chain" else ""
                with col:
                    st.markdown(f"""
<div class="model-card">
  <div class="mc-header"><span class="mc-name">{label}</span>{badge}</div>
  <div class="mc-total">${total:,.0f}</div>
  <div class="mc-desc">{MODEL_DESCRIPTIONS[key]}</div>
</div>""", unsafe_allow_html=True)
                    if st.button("View details →", key=f"drill_{key}", use_container_width=True):
                        st.session_state.selected_model = key
                        st.session_state.local_params   = {}
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — MODEL DETAIL VIEW
# ══════════════════════════════════════════════════════════════════════════════
else:
    model_key  = st.session_state.selected_model
    model_name = MODELS[model_key]

    back_col, title_col = st.columns([1, 5])
    with back_col:
        if st.button("← Back", key="btn_back", use_container_width=True):
            st.session_state.selected_model = None
            st.session_state.local_params   = {}
            st.rerun()
    with title_col:
        st.markdown(f"## {model_name}")
        st.caption(MODEL_DESCRIPTIONS[model_key])
    st.markdown("---")

    # ── Parameters ────────────────────────────────────────────────────────────
    saved_p   = dict(DEFAULT_MODEL_PARAMS.get(model_key, {}))
    saved_p.update(model_settings.get(model_key, {}))
    local_p   = st.session_state.local_params.get(model_key, {})
    current_p = {**saved_p, **local_p}

    st.markdown("#### ⚙ Parameters")
    new_p = dict(current_p)

    if model_key in ("dod_chain", "adaptive_dow", "same_dow", "trend_dow"):
        lb_map = {"4 weeks": 4, "8 weeks": 8, "All history": None}
        lb_rev = {v: k for k, v in lb_map.items()}
        lb_cur = lb_rev.get(current_p.get("lookback_weeks", 8), "8 weeks")
        lb_sel = st.radio("Lookback window", list(lb_map.keys()), index=list(lb_map.keys()).index(lb_cur),
                          horizontal=True, key=f"lb_{model_key}")
        new_p["lookback_weeks"] = lb_map[lb_sel]

    if model_key == "dod_chain":
        new_p["use_trimmed_mean"] = st.checkbox(
            "Drop min/max outlier pairs (trimmed mean)",
            value=current_p.get("use_trimmed_mean", True),
            key="dod_trimmed",
        )

    if model_key == "ema_baseline":
        new_p["use_ewma"] = st.checkbox(
            "Use EWMA weighting for weekday multipliers",
            value=current_p.get("use_ewma", True),
            key="ema_use_ewma",
        )
        new_p["ema_span"] = st.slider(
            "EMA span (days)", 7, 30, value=int(current_p.get("ema_span", 14)), key="ema_span"
        )
        if new_p["use_ewma"]:
            new_p["ewma_halflife"] = st.slider(
                "EWMA half-life (weeks)", 1, 12, value=int(current_p.get("ewma_halflife", 4)),
                key="ema_halflife"
            )

    if model_key == "trend_dow":
        new_p["trend_lookback_weeks"] = st.slider(
            "Trend detection window (weeks)", 2, 8,
            value=int(current_p.get("trend_lookback_weeks", 4)),
            key="trend_lw",
        )

    if model_key == "ensemble":
        st.info("Ensemble is the median of all five other models. No parameters to tune.")

    # Track live param changes in session state (not yet saved)
    st.session_state.local_params[model_key] = {
        k: v for k, v in new_p.items() if v != saved_p.get(k)
    }

    unsaved = bool(st.session_state.local_params.get(model_key))
    if unsaved:
        st.caption("_Unsaved changes — chart reflects current values. Click Save to persist._")

    col_save, col_reset = st.columns(2)
    with col_save:
        if st.button("💾 Save Settings", use_container_width=True, key="btn_save_settings"):
            if _as_configured():
                try:
                    save_model_settings(model_key, new_p)
                    st.session_state.local_params[model_key] = {}
                    st.success("Settings saved for all users.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Save failed: {exc}")
            else:
                st.warning("Apps Script not configured — settings won't persist.")
    with col_reset:
        if st.button("Reset to Defaults", use_container_width=True, key="btn_reset"):
            if _as_configured():
                save_model_settings(model_key, {})
            st.session_state.local_params[model_key] = {}
            st.rerun()

    st.markdown("---")

    # ── Chart & projected total ───────────────────────────────────────────────
    if has_data:
        # Re-run just this model with current (possibly unsaved) params
        proj_fn_map = {
            "dod_chain":    project_dod_chain,
            "adaptive_dow": project_adaptive_dow,
            "same_dow":     project_same_dow,
            "ema_baseline": project_ema_baseline,
            "trend_dow":    project_trend_dow,
        }
        if model_key == "ensemble":
            proj_df = all_proj["ensemble"]
        else:
            proj_df = proj_fn_map[model_key](df, new_p, today)

        st.plotly_chart(make_chart(proj_df, model_name), use_container_width=True)

        # Summary metrics
        total_proj = projected_total(proj_df, actual_mtd)
        c1, c2 = st.columns(2)
        with c1:
            st.metric("MTD Actual",            f"${actual_mtd:,.0f}")
        with c2:
            st.metric("Projected Month Total", f"${total_proj:,.0f}")

        # DoW breakdown table
        with st.expander("📊 Day-of-Week Breakdown", expanded=False):
            dow_rows = []
            for d in DOW_SHORT:
                sub = proj_df[proj_df["date"].dt.strftime("%a") == d]
                act = sub[sub["type"] == "actual"]["spend"].sum()
                fut = sub[sub["type"] == "projected"]["spend"].mean()
                dow_rows.append({
                    "Day":            d,
                    "Actual (avg $)": f"${act:,.0f}" if act > 0 else "—",
                    "Projected (avg $)": f"${fut:,.0f}" if not np.isnan(fut) else "—",
                })
            st.dataframe(pd.DataFrame(dow_rows), use_container_width=True, hide_index=True)

        # Download full projection
        with st.expander("📥 Download Projection", expanded=False):
            dl = proj_df[["date", "spend", "type"]].copy()
            dl["date"] = dl["date"].dt.strftime("%Y-%m-%d")
            dl.columns = ["Date", "Spend ($)", "Type"]
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
                dl.to_excel(writer, index=False, sheet_name="Projection")
            st.download_button(
                "Download Excel",
                data=buf.getvalue(),
                file_name=f"projection_{model_key}_{today}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    else:
        st.info("No spend data loaded yet. Add historical data via the sidebar.")
