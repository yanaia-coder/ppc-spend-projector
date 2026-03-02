"""
PPC Spend Projector — Streamlit Web Edition
Three models: Adaptive DoW ★ · Same-DoW Avg · EMA Baseline
Tailored for Google & Bing Search Ads.
"""

import calendar
from io import BytesIO

import numpy as np
import pandas as pd
import plotly.graph_objects as go
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif !important; }

/* ── App background — force light even if OS/Streamlit is in dark mode ──────── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section[data-testid="stMain"] > div {
    background-color: #f1f5f9 !important;
    color: #1f2937 !important;
}
.main .block-container { padding-top: 2rem; padding-bottom: 3rem; }

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

/* ── BUTTONS — cast-iron rules that survive theme switching ─────────────────── */

/* 1. Every button on the page — base state */
button[kind="secondary"],
button[kind="primary"],
.stButton button,
div[data-testid="stButton"] button,
div[data-testid="stBaseButton-secondary"] button,
div[data-testid="stBaseButton-primary"] button {
    background-color: #2563eb !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    transition: background-color 0.15s ease, box-shadow 0.15s ease !important;
    box-shadow: 0 1px 4px rgba(37, 99, 235, 0.35) !important;
}
/* Force the text node inside buttons to be white (catches both p and span wrappers) */
.stButton button p,
.stButton button span,
div[data-testid="stButton"] button p,
div[data-testid="stButton"] button span,
div[data-testid="stBaseButton-secondary"] button p,
div[data-testid="stBaseButton-secondary"] button span,
div[data-testid="stBaseButton-primary"] button p,
div[data-testid="stBaseButton-primary"] button span {
    color: #ffffff !important;
}

/* 2. Hover */
button[kind="secondary"]:hover,
button[kind="primary"]:hover,
.stButton button:hover,
div[data-testid="stButton"] button:hover,
div[data-testid="stBaseButton-secondary"] button:hover,
div[data-testid="stBaseButton-primary"] button:hover {
    background-color: #1d4ed8 !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.45) !important;
}
/* 3. Active (click) */
button[kind="secondary"]:active,
button[kind="primary"]:active,
.stButton button:active,
div[data-testid="stButton"] button:active,
div[data-testid="stBaseButton-secondary"] button:active,
div[data-testid="stBaseButton-primary"] button:active {
    background-color: #1e40af !important;
    color: #ffffff !important;
    box-shadow: none !important;
}
/* 4. Focus ring */
button[kind="secondary"]:focus-visible,
button[kind="primary"]:focus-visible,
.stButton button:focus-visible,
div[data-testid="stButton"] button:focus-visible,
div[data-testid="stBaseButton-secondary"] button:focus-visible,
div[data-testid="stBaseButton-primary"] button:focus-visible {
    background-color: #2563eb !important;
    color: #ffffff !important;
    outline: 2px solid #93c5fd !important;
    outline-offset: 2px !important;
    box-shadow: none !important;
}

/* ── Sidebar buttons — translucent indigo layer on top of base rules ─────────── */
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
[data-testid="stSidebar"] div[data-testid="stButton"] button span {
    color: #c7d2fe !important;
}
[data-testid="stSidebar"] .stButton button:hover,
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover,
[data-testid="stSidebar"] div[data-testid="stBaseButton-secondary"] button:hover {
    background-color: rgba(99, 102, 241, 0.42) !important;
    color: #ffffff !important;
    border-color: rgba(129, 140, 248, 0.65) !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton button:hover p,
[data-testid="stSidebar"] .stButton button:hover span,
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover p,
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover span {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stButton button:active,
[data-testid="stSidebar"] div[data-testid="stButton"] button:active {
    background-color: rgba(99, 102, 241, 0.6) !important;
    color: #ffffff !important;
}

/* ── Danger / Start Fresh button ─────────────────────────────────────────────── */
.danger-btn .stButton button,
.danger-btn div[data-testid="stButton"] button,
.danger-btn div[data-testid="stBaseButton-secondary"] button {
    background-color: rgba(220, 38, 38, 0.12) !important;
    color: #fca5a5 !important;
    border: 1px solid rgba(220, 38, 38, 0.28) !important;
    box-shadow: none !important;
}
.danger-btn .stButton button p,
.danger-btn .stButton button span,
.danger-btn div[data-testid="stButton"] button p,
.danger-btn div[data-testid="stButton"] button span {
    color: #fca5a5 !important;
}
.danger-btn .stButton button:hover,
.danger-btn div[data-testid="stButton"] button:hover,
.danger-btn div[data-testid="stBaseButton-secondary"] button:hover {
    background-color: rgba(220, 38, 38, 0.3) !important;
    color: #ffffff !important;
    border-color: rgba(220, 38, 38, 0.55) !important;
    box-shadow: none !important;
}
.danger-btn .stButton button:hover p,
.danger-btn .stButton button:hover span,
.danger-btn div[data-testid="stButton"] button:hover p,
.danger-btn div[data-testid="stButton"] button:hover span {
    color: #ffffff !important;
}
.danger-btn .stButton button:active,
.danger-btn div[data-testid="stButton"] button:active {
    background-color: rgba(220, 38, 38, 0.48) !important;
    color: #ffffff !important;
}

/* ── Metric cards — force high contrast text regardless of theme ─────────────── */
[data-testid="stMetric"] {
    background-color: #ffffff !important;
    border: 1px solid #e0e7ff !important;
    border-left: 5px solid #4f46e5 !important;
    border-radius: 12px !important;
    padding: 1.25rem 1.5rem 1rem !important;
    box-shadow: 0 4px 16px rgba(79, 70, 229, 0.08) !important;
    transition: box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 6px 24px rgba(79, 70, 229, 0.15) !important;
}
/* Label — every possible nested element */
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] span,
[data-testid="stMetricLabel"] div,
[data-testid="stMetricLabel"] label {
    color: #6366f1 !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
}
/* Value — every possible nested element */
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] p,
[data-testid="stMetricValue"] span,
[data-testid="stMetricValue"] div {
    color: #1f2937 !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

/* ── Page title elements ─────────────────────────────────────────────────────── */
.page-title {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    color: #1e1b4b !important;
    margin: 0 0 0.25rem !important;
    letter-spacing: -0.02em;
}
.page-badge {
    display: inline-block;
    background: #ede9fe !important;
    color: #5b21b6 !important;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 3px 10px;
    border-radius: 99px;
    margin-bottom: 0.5rem;
}
.page-subtitle { color: #64748b !important; font-size: 0.9rem; margin: 0; }
.month-chip {
    display: inline-block;
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: #ffffff !important;
    font-size: 0.85rem;
    font-weight: 600;
    padding: 4px 14px;
    border-radius: 99px;
    margin-bottom: 0.5rem;
}
.model-status {
    font-size: 0.78rem;
    color: #6366f1;
    font-weight: 600;
    letter-spacing: 0.04em;
    margin-bottom: 1rem;
}

/* ── Main area text — force dark on light ────────────────────────────────────── */
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

/* ── Dialog ──────────────────────────────────────────────────────────────────── */
[data-testid="stModal"] .stMarkdown h2 { color: #1e1b4b !important; margin-top: 1.2rem; }
[data-testid="stModal"] .stMarkdown h3 { color: #4f46e5 !important; margin-top: 1rem; }
[data-testid="stModal"] .stMarkdown code {
    background: #ede9fe !important;
    color: #5b21b6 !important;
    padding: 2px 6px;
    border-radius: 4px;
}
[data-testid="stModal"] .stMarkdown blockquote {
    border-left: 4px solid #4f46e5 !important;
    background: #f5f3ff !important;
    padding: 0.6rem 1rem;
    border-radius: 0 8px 8px 0;
    margin: 0.8rem 0;
}

/* ── Divider ─────────────────────────────────────────────────────────────────── */
hr { border-color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MATH CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
DOW_ORDER = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday",
]

DEFAULT_PARAMS: dict = {
    "model":          "adaptive_same_dow",
    "lookback_weeks": 8,
    "ema_span":       14,
    "use_ewma":       True,
    "ewma_halflife":  4,
}

MODEL_LABELS = {
    "Adaptive DoW ★": "adaptive_same_dow",
    "Same-DoW Avg":   "same_dow",
    "EMA Baseline":   "ema_baseline",
}
MODEL_LABELS_INV = {v: k for k, v in MODEL_LABELS.items()}


# ══════════════════════════════════════════════════════════════════════════════
# MATH HELPERS  (ported verbatim from desktop_app.py v4.0)
# ══════════════════════════════════════════════════════════════════════════════

def _same_dow_averages(df: pd.DataFrame, lookback_weeks) -> dict:
    """
    For each weekday compute the robust average spend over the last N actual
    occurrences of that weekday.  lookback_weeks=None → all history.
    Returns {dow_name: {"avg": float, "count": int}}
    """
    result: dict = {}
    for dow in DOW_ORDER:
        series = df[df["DayOfWeek"] == dow]["Spend"]
        if lookback_weeks is not None:
            series = series.tail(lookback_weeks)
        y = series.values.astype(float)
        n = len(y)
        if n == 0:
            result[dow] = {"avg": 0.0, "count": 0}
            continue
        trimmed = np.sort(y)[1:-1] if n >= 6 else y
        result[dow] = {"avg": float(np.mean(trimmed)), "count": n}
    return result


def _week_scale_factor(df: pd.DataFrame, dow_avgs: dict) -> float:
    """
    Compare the last 7 actual days to what Same-DoW would have predicted.
    Returns a scale factor capped at [0.50, 2.00].
    """
    recent = df.tail(7)
    ratios = []
    for _, row in recent.iterrows():
        predicted = dow_avgs.get(row["DayOfWeek"], {}).get("avg", 0.0)
        if predicted > 0:
            ratios.append(float(row["Spend"]) / predicted)
    if not ratios:
        return 1.0
    scale = float(np.median(ratios))
    return max(0.5, min(2.0, scale))


def _compute_dow_multipliers_equal(df: pd.DataFrame) -> pd.Series:
    global_avg = df["Spend"].mean()
    if global_avg == 0:
        raise ValueError("Average spend is zero — cannot compute multipliers.")
    dow_avg = df.groupby("DayOfWeek")["Spend"].mean()
    return (dow_avg / global_avg).reindex(DOW_ORDER).fillna(1.0)


def _compute_dow_multipliers_ewma(df: pd.DataFrame, halflife_weeks: int = 4) -> pd.Series:
    last_date     = df["Date"].max()
    halflife_days = halflife_weeks * 7
    decay         = np.log(2) / halflife_days
    df = df.copy()
    df["_w"] = np.exp(-decay * (last_date - df["Date"]).dt.days.astype(float))
    global_wmean = float(np.average(df["Spend"], weights=df["_w"]))
    if global_wmean == 0:
        raise ValueError("Weighted average spend is zero.")
    mults: dict = {}
    for dow in DOW_ORDER:
        mask = df["DayOfWeek"] == dow
        mults[dow] = (
            float(np.average(df.loc[mask, "Spend"], weights=df.loc[mask, "_w"]))
            / global_wmean
            if mask.any() else 1.0
        )
    return pd.Series(mults).reindex(DOW_ORDER).fillna(1.0)


# ══════════════════════════════════════════════════════════════════════════════
# PACING MATH
# ══════════════════════════════════════════════════════════════════════════════
def run_pacing_math(df: pd.DataFrame, params: dict | None = None) -> dict:
    """
    Three projection models tailored for PPC search ads.
    Handles data cleaning internally.
    """
    p              = {**DEFAULT_PARAMS, **(params or {})}
    model          = p["model"]
    lookback_weeks = p["lookback_weeks"]
    ema_span       = int(p["ema_span"])
    use_ewma       = bool(p["use_ewma"])
    ewma_halflife  = int(p["ewma_halflife"])

    date_col = next(
        (c for c in df.columns if c.strip().lower() in {"date", "date created"}), None
    )
    spend_col = next(
        (c for c in df.columns if c.strip().lower() in {"spend", "cost", "amount"}), None
    )
    if not date_col:
        raise ValueError(f"No 'Date' column found.\nColumns: {list(df.columns)}")
    if not spend_col:
        raise ValueError(f"No 'Spend' / 'Cost' / 'Amount' column found.\nColumns: {list(df.columns)}")

    df = df.copy()
    df[spend_col] = df[spend_col].astype(str).str.replace(r"[\$,\s]", "", regex=True)
    df[spend_col] = pd.to_numeric(df[spend_col], errors="coerce").fillna(0.0)
    df[date_col]  = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    df = df.rename(columns={date_col: "Date", spend_col: "Spend"})
    df["DayOfWeek"] = df["Date"].dt.day_name()

    last_date   = df["Date"].max()
    next_day    = last_date + pd.Timedelta(days=1)
    ay, am      = next_day.year, next_day.month
    month_start = pd.Timestamp(ay, am, 1)
    month_end   = pd.Timestamp(ay, am, calendar.monthrange(ay, am)[1])

    mtd_mask   = (df["Date"] >= month_start) & (df["Date"] <= last_date)
    mtd_df     = df.loc[mtd_mask, ["Date", "Spend"]].copy()
    mtd_actual = float(mtd_df["Spend"].sum())

    proj_dates = pd.date_range(start=next_day, end=month_end, freq="D")
    week_scale = 1.0

    if model in ("adaptive_same_dow", "same_dow"):
        dow_avgs = _same_dow_averages(df, lookback_weeks)

        if model == "adaptive_same_dow":
            week_scale = _week_scale_factor(df, dow_avgs)

        proj_rows = [
            {
                "Date":            d,
                "Day of Week":     d.day_name(),
                "Historical Avg":  round(dow_avgs.get(d.day_name(), {}).get("avg", 0.0), 2),
                "Projected Spend": round(
                    dow_avgs.get(d.day_name(), {}).get("avg", 0.0) * week_scale, 2
                ),
            }
            for d in proj_dates
        ]
        proj_df = pd.DataFrame(
            proj_rows or [],
            columns=["Date", "Day of Week", "Historical Avg", "Projected Spend"],
        )

        if model == "adaptive_same_dow":
            dow_display = {
                dow: {
                    "col2": f"${dow_avgs[dow]['avg']:,.2f}",
                    "col3": f"${dow_avgs[dow]['avg'] * week_scale:,.2f}",
                }
                for dow in DOW_ORDER
            }
            dow_display_headers = ("Day of Week", "Historical Avg", "Adjusted Proj.")
        else:
            dow_display = {
                dow: {
                    "col2": f"${dow_avgs[dow]['avg']:,.2f}",
                    "col3": f"{dow_avgs[dow]['count']} wks",
                }
                for dow in DOW_ORDER
            }
            dow_display_headers = ("Day of Week", "Avg Spend", "Sample Weeks")

        dow_multipliers = pd.Series({dow: dow_avgs[dow]["avg"] for dow in DOW_ORDER})

    else:  # ema_baseline
        ema_series  = df["Spend"].ewm(span=ema_span, adjust=False).mean()
        baseline    = float(ema_series.iloc[-1])
        dow_multipliers = (
            _compute_dow_multipliers_ewma(df, ewma_halflife)
            if use_ewma
            else _compute_dow_multipliers_equal(df)
        )
        dow_dict = dow_multipliers.to_dict()
        proj_rows = [
            {
                "Date":            d,
                "Day of Week":     d.day_name(),
                "Multiplier":      round(float(dow_dict.get(d.day_name(), 1.0)), 4),
                "Projected Spend": round(
                    baseline * float(dow_dict.get(d.day_name(), 1.0)), 2
                ),
            }
            for d in proj_dates
        ]
        proj_df = pd.DataFrame(
            proj_rows or [],
            columns=["Date", "Day of Week", "Multiplier", "Projected Spend"],
        )
        dow_display = {
            dow: {
                "col2": f"×{float(dow_multipliers.get(dow, 1.0)):.4f}",
                "col3": f"{(float(dow_multipliers.get(dow, 1.0)) - 1) * 100:+.1f}%",
            }
            for dow in DOW_ORDER
        }
        dow_display_headers = ("Day of Week", "Multiplier", "vs. Average")

    projected_remaining = float(proj_df["Projected Spend"].sum())
    total_estimated     = mtd_actual + projected_remaining

    pm       = am - 1 if am > 1 else 12
    py       = ay if am > 1 else ay - 1
    pm_start = pd.Timestamp(py, pm, 1)
    pm_end   = pd.Timestamp(py, pm, calendar.monthrange(py, pm)[1])
    pm_mask  = (df["Date"] >= pm_start) & (df["Date"] <= pm_end)
    prev_df  = df.loc[pm_mask, ["Date", "Spend"]].copy()
    prev_df["DayNum"] = prev_df["Date"].dt.day

    return {
        "df":                   df,
        "model":                model,
        "week_scale":           week_scale,
        "dow_multipliers":      dow_multipliers,
        "dow_display":          dow_display,
        "dow_display_headers":  dow_display_headers,
        "last_date":            last_date,
        "active_year":          ay,
        "active_month":         am,
        "month_start":          month_start,
        "month_end":            month_end,
        "mtd_df":               mtd_df,
        "mtd_actual":           mtd_actual,
        "proj_df":              proj_df,
        "projected_remaining":  projected_remaining,
        "total_estimated":      total_estimated,
        "prev_df":              prev_df,
        "prev_month_start":     pm_start,
        "params":               p,
    }


# ══════════════════════════════════════════════════════════════════════════════
# HOW IT WORKS  —  dynamically reflects current model (ported from desktop_app.py)
# ══════════════════════════════════════════════════════════════════════════════
def get_how_it_works_steps(params: dict) -> list:
    p      = {**DEFAULT_PARAMS, **params}
    model  = p["model"]
    weeks  = p["lookback_weeks"]
    ewma   = bool(p["use_ewma"])
    hl     = int(p["ewma_halflife"])
    wk_str = f"last {weeks} weeks" if weeks else "all available history"

    tomorrow_rule = {
        "title": "📅  Step 1 — Active Month  (Tomorrow Rule)",
        "body":  (
            "The active month is the month of the day AFTER your last data row:\n\n"
            "  •  Data ends Feb 28  →  Active Month = March\n"
            "  •  Data ends Mar 31  →  Active Month = April\n\n"
            "Every remaining day in that month gets a projection."
        ),
    }

    if model == "adaptive_same_dow":
        return [
            tomorrow_rule,
            {
                "title": f"📊  Step 2 — Per-Weekday Historical Averages  ({wk_str})",
                "body":  (
                    f"For each weekday, the model computes the average actual spend "
                    f"over the {wk_str} of data:\n\n"
                    "  •  Monday avg  →  avg of the last "
                    + (f"{weeks} Mondays" if weeks else "all Mondays")
                    + "\n  •  Friday avg  →  avg of the last "
                    + (f"{weeks} Fridays" if weeks else "all Fridays")
                    + "\n\nOutliers: when a weekday has 6+ data points, the single "
                    "highest and lowest days are dropped before averaging."
                ),
            },
            {
                "title": "⚡  Step 3 — This-Week Scale Factor  (real-time adjustment)",
                "body":  (
                    "The model then checks how this week is performing vs. the historical baseline:\n\n"
                    "    Ratio(day) = Actual Spend ÷ Historical DoW Avg\n"
                    "    Scale Factor = Median of all ratios in the last 7 days\n\n"
                    "Examples:\n"
                    "  •  Scale = 1.18 → this week running 18% above historical\n"
                    "  •  Scale = 0.85 → this week running 15% below historical\n\n"
                    "The scale factor is capped between 0.50 and 2.00 to prevent "
                    "a single unusual week from causing wild projections.\n\n"
                    "This makes the model react immediately when you change a budget, "
                    "add campaigns, or experience seasonal shifts — without waiting "
                    "for N new weeks of data."
                ),
            },
            {
                "title": "🔢  Step 4 — Daily Projection",
                "body":  (
                    "    Projected Spend(day D) = Historical DoW Avg × Scale Factor\n\n"
                    "The historical average defines the weekly shape; the scale factor "
                    "shifts the entire projection up or down to match current account performance."
                ),
            },
            {
                "title": "💰  Step 5 — MTD Actuals",
                "body":  (
                    "The sum of actual spend from the 1st of the Active Month up to your "
                    "last data row. Can be $0 if data ends on the last day of the previous month."
                ),
            },
            {
                "title": "🎯  Step 6 — Total Estimated Month Spend",
                "body":  (
                    "  Total = MTD Actuals + Sum of All Projected Remaining Days\n\n"
                    f"Combines confirmed actuals with adaptive DoW projections "
                    f"({wk_str} lookback, real-time scale adjustment)."
                ),
            },
        ]

    elif model == "same_dow":
        return [
            tomorrow_rule,
            {
                "title": f"📊  Step 2 — Per-Weekday Averages  ({wk_str})",
                "body":  (
                    f"For each weekday, the model averages the actual spend over the "
                    f"{wk_str}:\n\n"
                    "  •  Next Monday  =  avg of the last "
                    + (f"{weeks} Mondays" if weeks else "all Mondays") + "\n"
                    "  •  Next Friday  =  avg of the last "
                    + (f"{weeks} Fridays" if weeks else "all Fridays") + "\n\n"
                    "No baseline scaling, no multipliers, no trend. "
                    "Day-of-week pattern is embedded directly. "
                    "Single highest and lowest days dropped when 6+ samples exist."
                ),
            },
            {
                "title": "🔢  Step 3 — Daily Projection",
                "body": "    Projected Spend(day D) = Historical Avg for D's weekday",
            },
            {
                "title": "💰  Step 4 — MTD Actuals",
                "body": (
                    "Sum of actual spend from the 1st of the Active Month to your last data row."
                ),
            },
            {
                "title": "🎯  Step 5 — Total Estimated Month Spend",
                "body": (
                    "  Total = MTD Actuals + Sum of All Projected Remaining Days\n\n"
                    f"Stable and transparent — uses pure historical DoW averages "
                    f"({wk_str} lookback), no real-time adjustment."
                ),
            },
        ]

    else:  # ema_baseline
        return [
            tomorrow_rule,
            {
                "title": "📐  Step 2 — Day-of-Week Multipliers",
                "body":  (
                    "Calculated from ALL historical data"
                    + (f" with exponential weighting ({hl}-week half-life)" if ewma else "")
                    + ":\n\n"
                    "  Multiplier(DoW) = "
                    + ("Weighted " if ewma else "") + "Mean(Spend on that DoW)  ÷  "
                    + ("Weighted " if ewma else "") + "Global Daily Mean\n\n"
                    + (
                        f"A Monday from {hl} weeks ago counts half as much as last Monday."
                        if ewma else "All historical days are weighted equally."
                    )
                ),
            },
            {
                "title": f"📊  Step 3 — EMA Baseline  (span: {p['ema_span']} days)",
                "body":  (
                    f"An Exponential Moving Average over {p['ema_span']} days of actual spend. "
                    "EMA weights recent days much more heavily than older ones — "
                    "so the baseline responds quickly when you raise or lower budgets, "
                    "without extrapolating a false linear trend."
                ),
            },
            {
                "title": "🔢  Step 4 — Daily Projection",
                "body": (
                    "    Projected Spend = EMA Baseline × Multiplier(Day of Week)\n\n"
                    "EMA baseline sets the spending level; DoW multiplier adds weekly rhythm."
                ),
            },
            {
                "title": "💰  Step 5 — MTD Actuals",
                "body": "Sum of actual spend from the 1st of the Active Month to your last data row.",
            },
            {
                "title": "🎯  Step 6 — Total Estimated Month Spend",
                "body": (
                    "  Total = MTD Actuals + Sum of All Projected Remaining Days\n\n"
                    "Based on EMA baseline"
                    + (" + exponentially-weighted DoW multipliers." if ewma
                       else " + equal-weight DoW multipliers.")
                ),
            },
        ]


# ══════════════════════════════════════════════════════════════════════════════
# DIALOG — How the Math Works
# ══════════════════════════════════════════════════════════════════════════════
@st.dialog("🧠 How the Math Works", width="large")
def show_explainer(params: dict):
    p = {**DEFAULT_PARAMS, **params}
    model_label = MODEL_LABELS_INV.get(p["model"], p["model"])
    wk = p["lookback_weeks"]

    if p["model"] in ("adaptive_same_dow", "same_dow"):
        badge = f"**Model:** {model_label}  ·  **Lookback:** {f'{wk} wks' if wk else 'all history'}"
    elif p["use_ewma"]:
        badge = f"**Model:** {model_label}  ·  **Weighted DoW** ({p['ewma_halflife']}w half-life)"
    else:
        badge = f"**Model:** {model_label}  ·  Equal-weight DoW"

    st.markdown(badge)
    st.divider()

    for step in get_how_it_works_steps(params):
        st.markdown(f"### {step['title']}")
        st.code(step["body"], language=None)


# ══════════════════════════════════════════════════════════════════════════════
# PASSWORD GATE
# APP_PASSWORD is set in Streamlit Cloud → App Settings → Secrets (never in code).
# If absent (local dev), the gate is skipped automatically.
# ══════════════════════════════════════════════════════════════════════════════
_app_password = st.secrets.get("APP_PASSWORD", "")
if _app_password:
    _entered = st.text_input("🔒 Enter password to access this app", type="password")
    if _entered != _app_password:
        st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
if "uploader_counter" not in st.session_state:
    st.session_state["uploader_counter"] = 0


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # ── Branding ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 0.5rem 0 0.25rem;">
        <div style="font-size:2.2rem; margin-bottom:0.2rem;">📊</div>
        <div style="font-size:1.1rem; font-weight:700; color:#ffffff; letter-spacing:-0.01em;">
            PPC Spend Projector
        </div>
        <div style="font-size:0.72rem; color:#818cf8; margin-top:0.2rem;">
            GOOGLE &amp; BING SEARCH ADS
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── 📁 Data Input ───────────────────────────────────────────────────────────
    st.markdown("#### 📁 Data Input")

    df_raw = None
    uploaded = st.file_uploader(
        "Upload your spend data (.csv or .xlsx)",
        type=["csv", "xlsx"],
        key=f"file_uploader_{st.session_state['uploader_counter']}",
    )
    if uploaded:
        try:
            df_raw = (
                pd.read_excel(uploaded)
                if uploaded.name.endswith(".xlsx")
                else pd.read_csv(uploaded)
            )
            st.success(f"✅ Loaded: `{uploaded.name}`")
        except Exception as exc:
            st.error(f"Could not read file.\n\n{exc}")

    st.markdown("""
    <div style="color:#6366f1; font-size:0.75rem; margin-top:0.6rem; line-height:1.7;">
        Requires columns:<br>
        <code style="background:rgba(99,102,241,0.2);color:#a5b4fc;padding:1px 5px;
        border-radius:3px;">Date</code>&nbsp;or&nbsp;
        <code style="background:rgba(99,102,241,0.2);color:#a5b4fc;padding:1px 5px;
        border-radius:3px;">Date Created</code><br>
        <code style="background:rgba(99,102,241,0.2);color:#a5b4fc;padding:1px 5px;
        border-radius:3px;">Spend</code>&nbsp;/&nbsp;
        <code style="background:rgba(99,102,241,0.2);color:#a5b4fc;padding:1px 5px;
        border-radius:3px;">Cost</code>&nbsp;/&nbsp;
        <code style="background:rgba(99,102,241,0.2);color:#a5b4fc;padding:1px 5px;
        border-radius:3px;">Amount</code>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── 🔢 Projection Model ──────────────────────────────────────────────────────
    st.markdown("#### 🔢 Projection Model")

    model_label = st.radio(
        "",
        list(MODEL_LABELS.keys()),
        index=0,
        label_visibility="collapsed",
    )
    model_key = MODEL_LABELS[model_label]

    if model_key in ("adaptive_same_dow", "same_dow"):
        lookback_choice = st.selectbox(
            "DoW Lookback",
            ["4 wks", "8 wks (default)", "All"],
            index=1,
        )
        lookback_weeks = {"4 wks": 4, "8 wks (default)": 8, "All": None}[lookback_choice]
        use_ewma = True  # not used by these models
    else:  # ema_baseline
        lookback_weeks = 8  # not used by EMA
        use_ewma = st.toggle("Weighted DoW (4-wk half-life)", value=True)

    params = {
        "model":          model_key,
        "lookback_weeks": lookback_weeks,
        "use_ewma":       use_ewma,
    }

    st.divider()

    # ── ℹ️ About ─────────────────────────────────────────────────────────────────
    st.markdown("#### ℹ️ About")
    if st.button("🧠 How the Math Works", use_container_width=True):
        show_explainer(params)

    st.divider()

    # ── 🗑️ Reset ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="color:#94a3b8; font-size:0.72rem; margin-bottom:0.5rem; text-align:center;">
        Clear all data and start over
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
    if st.button("🗑️ Start Fresh / Clear Data", use_container_width=True):
        next_counter = st.session_state["uploader_counter"] + 1
        st.session_state.clear()
        st.session_state["uploader_counter"] = next_counter
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — Header
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="margin-bottom: 1.5rem;">
    <div class="page-badge">Monthly Budget Pacing</div>
    <p class="page-title">PPC Spend Projector</p>
    <p class="page-subtitle">Upload a spend file in the sidebar to generate a projection.</p>
</div>
""", unsafe_allow_html=True)

if df_raw is None:
    st.info("👈 Upload a .csv or .xlsx file in the sidebar to get started.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# RUN MATH
# ══════════════════════════════════════════════════════════════════════════════
try:
    result = run_pacing_math(df_raw, params)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

df            = result["df"]
model         = result["model"]
week_scale    = result["week_scale"]
last_date     = result["last_date"]
ay            = result["active_year"]
am            = result["active_month"]
month_start   = result["month_start"]
month_end     = result["month_end"]
mtd_df        = result["mtd_df"]
mtd_actual    = result["mtd_actual"]
proj_df       = result["proj_df"]
total_estimated = result["total_estimated"]
prev_df       = result["prev_df"]
pm_start      = result["prev_month_start"]
dow_display   = result["dow_display"]
dow_display_headers = result["dow_display_headers"]


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD — Active Month + Model Status
# ══════════════════════════════════════════════════════════════════════════════
active_label = month_start.strftime("%B %Y")

st.markdown(
    f'<div class="month-chip">📅 Active Month: {active_label}</div>',
    unsafe_allow_html=True,
)

if model == "adaptive_same_dow":
    status_text = f"Adaptive DoW ★  ·  this-week ×{week_scale:.2f}  ·  lookback {lookback_weeks or 'all'} wks"
elif model == "same_dow":
    status_text = f"Same-DoW Avg  ·  lookback {lookback_weeks or 'all'} wks"
else:
    status_text = f"EMA Baseline  ·  {'weighted' if use_ewma else 'equal'} DoW"

st.markdown(f'<div class="model-status">{status_text}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD — Metrics
# ══════════════════════════════════════════════════════════════════════════════
col1, col2 = st.columns(2)
col1.metric("MTD Actual Spend", f"${mtd_actual:,.2f}")
col2.metric("Total Estimated Month Spend", f"${total_estimated:,.2f}")

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD — Pacing Chart
# ══════════════════════════════════════════════════════════════════════════════
chart_title_col, chart_ctrl_col = st.columns([3, 1])
with chart_title_col:
    st.subheader("Pacing Chart")
with chart_ctrl_col:
    st.markdown("<div style='margin-top:0.55rem;'></div>", unsafe_allow_html=True)
    show_prev_month = st.checkbox(
        "Compare to Previous Month",
        value=False,
        help="Overlay last month's actual daily spend, aligned by day-of-month",
    )

CLR_ACTUAL    = "#4f46e5"
CLR_ACTUAL_BG = "rgba(79,70,229,0.10)"
CLR_PROJ      = "#f59e0b"

fig = go.Figure()

if not mtd_df.empty:
    fig.add_trace(go.Scatter(
        x=mtd_df["Date"],
        y=mtd_df["Spend"],
        mode="lines+markers",
        name="Actual Spend",
        fill="tozeroy",
        fillcolor=CLR_ACTUAL_BG,
        line=dict(color=CLR_ACTUAL, width=2.5, shape="spline", smoothing=0.7),
        marker=dict(size=5, color=CLR_ACTUAL, line=dict(width=1.5, color="#ffffff")),
        hovertemplate="<b>%{x|%b %d}</b><br>Actual: <b>$%{y:,.2f}</b><extra></extra>",
    ))

if not proj_df.empty:
    if not mtd_df.empty:
        cx = [last_date] + proj_df["Date"].tolist()
        cy = [float(mtd_df["Spend"].iloc[-1])] + proj_df["Projected Spend"].tolist()
    else:
        cx = proj_df["Date"].tolist()
        cy = proj_df["Projected Spend"].tolist()

    fig.add_trace(go.Scatter(
        x=cx,
        y=cy,
        mode="lines+markers",
        name="Projected Spend",
        line=dict(color=CLR_PROJ, width=2.5, dash="dash"),
        marker=dict(size=5, symbol="circle-open", color=CLR_PROJ, line=dict(width=2)),
        hovertemplate="<b>%{x|%b %d}</b><br>Projected: <b>$%{y:,.2f}</b><extra></extra>",
    ))

if show_prev_month and not prev_df.empty:
    max_day = month_end.day
    prev_plot = prev_df[prev_df["DayNum"] <= max_day].copy()
    prev_plot["PlotDate"] = prev_plot["DayNum"].apply(
        lambda d: pd.Timestamp(ay, am, d)
    )
    prev_plot["ActualDateStr"] = prev_plot["Date"].dt.strftime("%b %d, %Y")
    prev_label = pm_start.strftime("%b %Y")
    fig.add_trace(go.Scatter(
        x=prev_plot["PlotDate"],
        y=prev_plot["Spend"],
        customdata=prev_plot["ActualDateStr"],
        mode="lines",
        name=f"Prev. Month ({prev_label})",
        line=dict(color="#94a3b8", width=1.5, dash="dot"),
        opacity=0.75,
        hovertemplate=(
            "<b>Prev. Month — %{customdata}</b>"
            "<br>Spend: $%{y:,.2f}<extra></extra>"
        ),
    ))

fig.update_layout(
    height=460,
    margin=dict(l=0, r=0, t=72, b=0),
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="#1e1b4b",
        font_color="#ffffff",
        font_size=13,
        bordercolor="#1e1b4b",
        namelength=-1,
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="right", x=1,
        font=dict(size=12, color="#334155"),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="rgba(0,0,0,0)",
    ),
    xaxis=dict(
        title=None,
        showgrid=False,
        showline=False, zeroline=False,
        tickformat="%b %d", tickangle=-30,
        tickfont=dict(size=11, color="#64748b"),
        range=[
            month_start - pd.Timedelta(hours=12),
            month_end + pd.Timedelta(hours=12),
        ],
    ),
    yaxis=dict(
        title="Daily Spend",
        tickprefix="$", tickformat=",.0f",
        showgrid=True, gridcolor="#ececf3", gridwidth=1,
        showline=False, zeroline=False,
        rangemode="tozero",
        tickfont=dict(size=11, color="#64748b"),
        title_font=dict(size=12, color="#94a3b8"),
    ),
    font=dict(family="Inter, system-ui, sans-serif"),
)

st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# COLLAPSIBLE SECTIONS
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("📐 Day-of-Week Breakdown", expanded=False):
    h1, h2, h3 = dow_display_headers
    table_rows = [
        {h1: dow, h2: dow_display[dow]["col2"], h3: dow_display[dow]["col3"]}
        for dow in DOW_ORDER
        if dow in dow_display
    ]
    st.dataframe(
        pd.DataFrame(table_rows),
        use_container_width=False,
        hide_index=True,
    )
    if model == "adaptive_same_dow":
        st.caption(
            f"Scale factor this week: **×{week_scale:.2f}**  ·  "
            f"Derived from **{len(df):,}** days of history."
        )
    else:
        st.caption(f"Derived from **{len(df):,}** days of history.")

with st.expander("⬇ Download Projection", expanded=False):
    if proj_df.empty:
        st.info("No remaining days to project — the active month may already be complete.")
    else:
        export_df = proj_df.copy()
        export_df["Date"] = export_df["Date"].dt.strftime("%Y-%m-%d")

        filename_base = f"spend_projection_{ay}_{am:02d}"
        csv_bytes = export_df.to_csv(index=False).encode("utf-8")

        xlsx_buf = BytesIO()
        with pd.ExcelWriter(xlsx_buf, engine="xlsxwriter") as writer:
            export_df.to_excel(writer, index=False, sheet_name="Projection")
            wb, ws = writer.book, writer.sheets["Projection"]
            hdr_fmt = wb.add_format({
                "bold": True, "bg_color": "#4f46e5", "font_color": "#ffffff", "border": 0,
            })
            currency_fmt = wb.add_format({"num_format": "$#,##0.00"})
            for col_num, val in enumerate(export_df.columns):
                ws.write(0, col_num, val, hdr_fmt)
            ws.set_column("A:A", 13)
            ws.set_column("B:B", 15)
            last_col_idx = len(export_df.columns) - 1
            ws.set_column(last_col_idx, last_col_idx, 18, currency_fmt)
        xlsx_bytes = xlsx_buf.getvalue()

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "⬇ Download as CSV", csv_bytes,
                f"{filename_base}.csv", "text/csv",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                "⬇ Download as Excel (.xlsx)", xlsx_bytes,
                f"{filename_base}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

with st.expander("🔍 Data Preview (last 30 rows)", expanded=False):
    st.dataframe(
        df[["Date", "DayOfWeek", "Spend"]]
        .tail(30)
        .rename(columns={"DayOfWeek": "Day of Week"}),
        use_container_width=True,
        hide_index=True,
    )
