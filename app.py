"""
PPC Spend Projector — v2.1
Six models · Session-based data · CSV / Excel upload + manual entry
No backend required — upload your historical CSV to get started.
"""

import calendar
from datetime import date, timedelta
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
# CSS  — only for custom HTML blocks (.hero, .model-card)
# Everything else is handled by .streamlit/config.toml
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif !important; }

/* ── Hero banner ── */
.hero {
    background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 24px rgba(37, 99, 235, 0.28);
}
.hero-eyebrow {
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #bfdbfe; margin-bottom: 0.35rem;
}
.hero-value {
    font-size: 3rem; font-weight: 800;
    color: #ffffff; letter-spacing: -0.04em;
    line-height: 1; margin-bottom: 0.2rem;
}
.hero-sub  { font-size: 0.82rem; color: #93c5fd; }
.hero-right { text-align: right; }
.hero-day  { font-size: 0.78rem; color: #93c5fd; margin-bottom: 0.65rem; }
.hero-bar-wrap {
    width: 200px; height: 5px;
    background: rgba(255,255,255,0.2);
    border-radius: 99px; overflow: hidden; margin-left: auto;
}
.hero-bar-fill {
    height: 100%; background: rgba(255,255,255,0.85); border-radius: 99px;
}

/* ── Model cards ── */
.model-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.25rem 1.4rem 1rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: box-shadow 0.15s, border-color 0.15s;
    min-height: 112px;
}
.model-card:hover { box-shadow: 0 4px 16px rgba(37,99,235,0.12); border-color: #93c5fd; }
.mc-eyebrow {
    font-size: 0.68rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: #9ca3af; margin-bottom: 0.15rem;
}
.mc-value {
    font-size: 2rem; font-weight: 800;
    color: #111827; letter-spacing: -0.03em;
    line-height: 1.05; margin-bottom: 0.2rem;
}
.mc-desc  { font-size: 0.7rem; color: #9ca3af; line-height: 1.4; }
.mc-badge {
    display: inline-block; background: #dbeafe; color: #1d4ed8;
    font-size: 0.58rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.07em;
    padding: 2px 7px; border-radius: 99px;
    vertical-align: middle; margin-left: 6px;
}

/* ── Empty-state card ── */
.empty-card {
    background: #ffffff; border: 1px solid #e5e7eb;
    border-radius: 14px; padding: 3rem 2rem;
    text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
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
    "dod_chain":    {"lookback_weeks": 8, "use_trimmed_mean": True},
    "adaptive_dow": {"lookback_weeks": 8},
    "same_dow":     {"lookback_weeks": 8},
    "ema_baseline": {"ema_span": 14, "use_ewma": True, "ewma_halflife": 4},
    "trend_dow":    {"lookback_weeks": 8, "trend_lookback_weeks": 4},
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
# DATA HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def history_to_df(history: dict) -> pd.DataFrame:
    """Convert {date_str: float} → sorted DataFrame with date / spend / dow."""
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
    """Parse CSV or Excel → {date_str: float}. Flexible column detection."""
    name = file.name.lower()
    df = pd.read_csv(file) if name.endswith(".csv") else pd.read_excel(file)

    date_col = spend_col = None
    for col in df.columns:
        cl = col.lower().strip()
        if date_col  is None and any(k in cl for k in ("date", "day")):
            date_col = col
        if spend_col is None and any(k in cl for k in ("spend", "cost", "amount", "revenue")):
            spend_col = col

    if date_col  is None: date_col  = df.columns[0]
    if spend_col is None: spend_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, spend_col])

    result: dict = {}
    for _, row in df.iterrows():
        d = row[date_col].strftime("%Y-%m-%d")
        try:
            result[d] = float(str(row[spend_col]).replace(",", "").replace("$", "").strip())
        except (ValueError, TypeError):
            continue
    return result


# ══════════════════════════════════════════════════════════════════════════════
# MATH — HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _same_dow_avg(df: pd.DataFrame, lookback_weeks) -> dict:
    if lookback_weeks:
        cutoff = df["date"].max() - pd.Timedelta(weeks=int(lookback_weeks))
        sub = df[df["date"] >= cutoff]
    else:
        sub = df
    avgs    = sub.groupby("dow")["spend"].mean().to_dict()
    overall = sub["spend"].mean() if not sub.empty else 0.0
    return {d: avgs.get(d, overall) for d in DOW_SHORT}


def _week_scale_factor(df: pd.DataFrame, dow_avg: dict) -> float:
    today_ts   = pd.Timestamp.today().normalize()
    week_start = today_ts - pd.Timedelta(days=today_ts.dayofweek)
    this_week  = df[df["date"] >= week_start]
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
    df2     = df.sort_values("date").copy()
    hl_days = halflife_weeks * 7
    n       = len(df2)
    weights = np.exp(-np.log(2) / hl_days * (n - 1 - np.arange(n)))
    df2["_w"] = weights
    grouped = df2.groupby("dow").apply(
        lambda g: (g["spend"] * g["_w"]).sum() / g["_w"].sum()
    )
    total = sum(grouped.get(d, 0.0) for d in DOW_SHORT)
    if total == 0:
        return {d: 1 / 7 for d in DOW_SHORT}
    return {d: grouped.get(d, 0.0) / total for d in DOW_SHORT}


# ══════════════════════════════════════════════════════════════════════════════
# MATH — MODEL PROJECTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _actual_dict(df: pd.DataFrame, year: int, month: int) -> dict:
    sub = df[(df["date"].dt.year == year) & (df["date"].dt.month == month)]
    return {row["date"].date(): row["spend"] for _, row in sub.iterrows()}


def _build_proj_df(all_days: list, actual: dict, today: date, projected_values: dict) -> pd.DataFrame:
    rows = []
    for d in all_days:
        if d in actual:
            rows.append({"date": pd.Timestamp(d), "spend": actual[d],                "type": "actual"})
        elif d < today:
            rows.append({"date": pd.Timestamp(d), "spend": None,     "type": "missing"})
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

    pairs: dict = {}
    for i in range(1, len(hist)):
        prev = hist.iloc[i - 1]
        curr = hist.iloc[i]
        gap  = (curr["date"] - prev["date"]).days
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

    year, month   = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    all_days      = [date(year, month, d) for d in range(1, days_in_month + 1)]
    actual        = _actual_dict(df, year, month)
    dow_avg       = _same_dow_avg(df, lookback)

    projected: dict = {}
    last_val = last_dow = None

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
            last_val, last_dow = actual[d], dow
        elif d >= today:
            if last_val is not None and last_dow is not None:
                val = last_val * ratios.get((last_dow, dow), 1.0)
            else:
                val = dow_avg.get(dow, 0.0)
            projected[d] = max(0.0, val)
            last_val, last_dow = projected[d], dow

    return _build_proj_df(all_days, actual, today, projected)


def project_adaptive_dow(df: pd.DataFrame, params: dict, today: date) -> pd.DataFrame:
    lookback = params.get("lookback_weeks", 8)
    dow_avg  = _same_dow_avg(df, lookback)
    scale    = _week_scale_factor(df, dow_avg)

    year, month   = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    all_days      = [date(year, month, d) for d in range(1, days_in_month + 1)]
    actual        = _actual_dict(df, year, month)

    projected = {d: max(0.0, dow_avg.get(d.strftime("%a"), 0.0) * scale)
                 for d in all_days if d >= today and d not in actual}
    return _build_proj_df(all_days, actual, today, projected)


def project_same_dow(df: pd.DataFrame, params: dict, today: date) -> pd.DataFrame:
    lookback = params.get("lookback_weeks", 8)
    dow_avg  = _same_dow_avg(df, lookback)

    year, month   = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    all_days      = [date(year, month, d) for d in range(1, days_in_month + 1)]
    actual        = _actual_dict(df, year, month)

    projected = {d: max(0.0, dow_avg.get(d.strftime("%a"), 0.0))
                 for d in all_days if d >= today and d not in actual}
    return _build_proj_df(all_days, actual, today, projected)


def project_ema_baseline(df: pd.DataFrame, params: dict, today: date) -> pd.DataFrame:
    use_ewma = params.get("use_ewma", True)
    ema_span = params.get("ema_span", 14)
    halflife = params.get("ewma_halflife", 4)

    hist    = df.sort_values("date").copy()
    ema_val = float(hist["spend"].ewm(span=ema_span).mean().iloc[-1])
    mults   = _dow_multipliers_ewma(df, halflife) if use_ewma else \
              _dow_multipliers_equal(_same_dow_avg(df, None))

    year, month   = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    all_days      = [date(year, month, d) for d in range(1, days_in_month + 1)]
    actual        = _actual_dict(df, year, month)
    total_weight  = sum(mults[d.strftime("%a")] for d in all_days)

    projected = {}
    for d in all_days:
        if d >= today and d not in actual:
            m = mults[d.strftime("%a")]
            projected[d] = max(0.0, ema_val * m * days_in_month / total_weight) \
                           if total_weight > 0 else 0.0
    return _build_proj_df(all_days, actual, today, projected)


def project_trend_dow(df: pd.DataFrame, params: dict, today: date) -> pd.DataFrame:
    lookback       = params.get("lookback_weeks", 8)
    trend_lookback = params.get("trend_lookback_weeks", 4)
    dow_avg        = _same_dow_avg(df, lookback)

    hist         = df.sort_values("date").copy()
    trend_cutoff = hist["date"].max() - pd.Timedelta(weeks=int(trend_lookback) * 2)
    trend_data   = hist[hist["date"] >= trend_cutoff].copy()

    slope = days_since_midpoint = 0
    if len(trend_data) >= 3:
        x = (trend_data["date"] - trend_data["date"].min()).dt.days.values.astype(float)
        y = trend_data["spend"].values.astype(float)
        slope = float(np.polyfit(x, y, 1)[0])
        midpoint_date = trend_data["date"].iloc[len(trend_data) // 2]
        days_since_midpoint = (pd.Timestamp(today) - midpoint_date).days

    year, month   = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    all_days      = [date(year, month, d) for d in range(1, days_in_month + 1)]
    actual        = _actual_dict(df, year, month)

    projected = {}
    for d in all_days:
        if d >= today and d not in actual:
            days_out = (d - today).days
            base = dow_avg.get(d.strftime("%a"), 0.0)
            projected[d] = max(0.0, base + slope * (days_since_midpoint + days_out))
    return _build_proj_df(all_days, actual, today, projected)


def run_all_models(df: pd.DataFrame, saved_settings: dict, local_overrides: dict, today: date) -> dict:
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
    results: dict = {key: fn(df, get_params(key), today) for key, fn in proj_fns.items()}

    year, month   = today.year, today.month
    days_in_month = calendar.monthrange(year, month)[1]
    all_days      = [date(year, month, d) for d in range(1, days_in_month + 1)]
    actual        = _actual_dict(df, year, month)

    ens_rows = []
    for d in all_days:
        if d in actual:
            ens_rows.append({"date": pd.Timestamp(d), "spend": actual[d],   "type": "actual"})
        elif d < today:
            ens_rows.append({"date": pd.Timestamp(d), "spend": None,        "type": "missing"})
        else:
            vals = []
            for key in proj_fns:
                row = results[key][results[key]["date"] == pd.Timestamp(d)]
                if not row.empty and row.iloc[0]["type"] == "projected":
                    v = row.iloc[0]["spend"]
                    if v is not None:
                        vals.append(v)
            ens_rows.append({"date": pd.Timestamp(d),
                             "spend": float(np.median(vals)) if vals else 0.0,
                             "type": "projected"})
    results["ensemble"] = pd.DataFrame(ens_rows)
    return results


def projected_total(proj_df: pd.DataFrame, actual_mtd: float) -> float:
    return actual_mtd + float(proj_df[proj_df["type"] == "projected"]["spend"].sum())


# ══════════════════════════════════════════════════════════════════════════════
# CHART
# ══════════════════════════════════════════════════════════════════════════════

def make_chart(proj_df: pd.DataFrame, model_name: str) -> go.Figure:
    actual = proj_df[proj_df["type"] == "actual"]
    future = proj_df[proj_df["type"] == "projected"]
    fig    = go.Figure()

    if not actual.empty:
        fig.add_trace(go.Scatter(
            x=actual["date"], y=actual["spend"],
            mode="lines+markers", name="Actual",
            line=dict(color="#2563eb", width=2.5),
            marker=dict(size=6, color="#2563eb"),
        ))

    if not future.empty:
        if not actual.empty:
            fig.add_trace(go.Scatter(
                x=[actual["date"].iloc[-1], future["date"].iloc[0]],
                y=[actual["spend"].iloc[-1], future["spend"].iloc[0]],
                mode="lines",
                line=dict(color="#93c5fd", width=2, dash="dot"),
                showlegend=False,
            ))
        fig.add_trace(go.Scatter(
            x=future["date"], y=future["spend"],
            mode="lines+markers", name="Projected",
            line=dict(color="#93c5fd", width=2, dash="dot"),
            marker=dict(size=5, symbol="circle-open", color="#2563eb"),
        ))

    fig.update_layout(
        title=dict(text=model_name, font=dict(size=15, color="#111827")),
        xaxis_title=None,
        yaxis_title="Daily Spend ($)",
        hovermode="x unified",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=50, b=10),
        yaxis=dict(tickprefix="$", tickformat=",.0f",
                   gridcolor="#f3f4f6", zerolinecolor="#e5e7eb"),
        xaxis=dict(gridcolor="#f3f4f6"),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
if "history"        not in st.session_state: st.session_state.history        = {}
if "model_settings" not in st.session_state: st.session_state.model_settings = {}
if "selected_model" not in st.session_state: st.session_state.selected_model = None
if "local_params"   not in st.session_state: st.session_state.local_params   = {}
if "uploader_ctr"   not in st.session_state: st.session_state.uploader_ctr   = 0


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOAD  (from session state — instant, no network)
# ══════════════════════════════════════════════════════════════════════════════
df    = history_to_df(st.session_state.history)
today = date.today()

has_data = len(df) >= 7

if has_data:
    all_proj   = run_all_models(df, st.session_state.model_settings,
                                st.session_state.local_params, today)
    year, month = today.year, today.month
    actual_mtd  = float(df[(df["date"].dt.year == year) &
                           (df["date"].dt.month == month)]["spend"].sum())
    model_totals = {k: projected_total(all_proj[k], actual_mtd) for k in MODELS}


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📊 PPC Projector")

    # Flash message
    if st.session_state.get("_flash"):
        ftype, fmsg = st.session_state._flash
        if   ftype == "success": st.success(fmsg)
        elif ftype == "error":   st.error(fmsg)
        else:                    st.warning(fmsg)
        st.session_state._flash = None

    if has_data:
        last = df.sort_values("date").iloc[-1]
        st.caption(f"{len(df)} entries · last: **{last['date'].strftime('%b %d, %Y')}**")

    st.divider()

    # ── Upload history ─────────────────────────────────────────────────────────
    st.markdown("#### Upload History")
    st.caption("CSV or Excel with **Date** and **Spend** columns.")
    up_file = st.file_uploader(
        "Choose file",
        type=["csv", "xlsx", "xls"],
        key=f"uploader_{st.session_state.uploader_ctr}",
        label_visibility="collapsed",
    )
    if up_file is not None:
        if st.button("Load File", use_container_width=True, key="btn_load"):
            try:
                new_entries = parse_upload(up_file)
                if new_entries:
                    st.session_state.history.update(new_entries)
                    st.session_state.uploader_ctr += 1
                    n = len(new_entries)
                    st.session_state._flash = ("success", f"Loaded {n} records.")
                    st.rerun()
                else:
                    st.error("No valid date/spend data found in the file.")
            except Exception as exc:
                st.error(f"Upload failed: {exc}")

    st.divider()

    # ── Add / edit single entry ────────────────────────────────────────────────
    st.markdown("#### Add / Edit Entry")
    with st.form("daily_entry", clear_on_submit=True):
        entry_date   = st.date_input("Date", value=today - timedelta(days=1), max_value=today)
        entry_amount = st.number_input("Amount ($)", min_value=0.0, step=100.0, format="%.2f")
        if st.form_submit_button("Save Entry", use_container_width=True):
            if entry_amount <= 0:
                st.session_state._flash = ("error", "Amount must be greater than $0.")
                st.rerun()
            else:
                st.session_state.history[entry_date.strftime("%Y-%m-%d")] = \
                    round(float(entry_amount), 2)
                st.session_state._flash = (
                    "success",
                    f"Saved ${entry_amount:,.0f} for {entry_date.strftime('%b %d')}",
                )
                st.rerun()

    st.divider()

    # ── Clear ─────────────────────────────────────────────────────────────────
    if has_data:
        if st.button("Clear Session Data", use_container_width=True, key="btn_clear"):
            st.session_state.history        = {}
            st.session_state.model_settings = {}
            st.session_state.local_params   = {}
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.selected_model is None:

    month_label = today.strftime("%B %Y")

    if not has_data:
        st.markdown(f"""
<div class="empty-card">
  <div style="font-size:2.5rem;margin-bottom:0.75rem">📊</div>
  <div style="font-size:1.15rem;font-weight:700;color:#111827;margin-bottom:0.5rem">{month_label}</div>
  <div style="font-size:0.9rem;color:#6b7280;line-height:1.7;max-width:380px;margin:0 auto">
    Upload a CSV or Excel file with your historical spend data using
    <strong>Upload History</strong> in the sidebar to get started.<br><br>
    Need at least 7 days of data to run the models.
  </div>
</div>""", unsafe_allow_html=True)

    else:
        days_total = calendar.monthrange(year, month)[1]
        pct = min(100, round(today.day / days_total * 100))

        # Hero
        st.markdown(f"""
<div class="hero">
  <div>
    <div class="hero-eyebrow">{month_label} · MTD Actual</div>
    <div class="hero-value">${actual_mtd:,.0f}</div>
    <div class="hero-sub">Day {today.day} of {days_total}</div>
  </div>
  <div class="hero-right">
    <div class="hero-day">{pct}% through the month</div>
    <div class="hero-bar-wrap">
      <div class="hero-bar-fill" style="width:{pct}%"></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        st.markdown("### Model Comparison — Projected Month Total")

        model_list = list(MODELS.items())
        for row_start in range(0, len(model_list), 2):
            c1, c2 = st.columns(2, gap="medium")
            for col, idx in [(c1, row_start), (c2, row_start + 1)]:
                if idx >= len(model_list):
                    continue
                key, label = model_list[idx]
                total = model_totals.get(key, 0.0)
                badge = '<span class="mc-badge">Default</span>' if key == "dod_chain" else ""
                with col:
                    st.markdown(f"""
<div class="model-card">
  <div class="mc-eyebrow">{label}{badge}</div>
  <div class="mc-value">${total:,.0f}</div>
  <div class="mc-desc">{MODEL_DESCRIPTIONS[key]}</div>
</div>""", unsafe_allow_html=True)
                    if st.button("View details →", key=f"drill_{key}",
                                 use_container_width=True):
                        st.session_state.selected_model = key
                        st.session_state.local_params   = {}
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — MODEL DETAIL
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
    st.divider()

    # Parameters
    saved_p   = dict(DEFAULT_MODEL_PARAMS.get(model_key, {}))
    saved_p.update(st.session_state.model_settings.get(model_key, {}))
    local_p   = st.session_state.local_params.get(model_key, {})
    current_p = {**saved_p, **local_p}
    new_p     = dict(current_p)

    st.markdown("#### Parameters")

    if model_key in ("dod_chain", "adaptive_dow", "same_dow", "trend_dow"):
        lb_map = {"4 weeks": 4, "8 weeks": 8, "All history": None}
        lb_rev = {v: k for k, v in lb_map.items()}
        lb_cur = lb_rev.get(current_p.get("lookback_weeks", 8), "8 weeks")
        lb_sel = st.radio("Lookback window", list(lb_map.keys()),
                          index=list(lb_map.keys()).index(lb_cur),
                          horizontal=True, key=f"lb_{model_key}")
        new_p["lookback_weeks"] = lb_map[lb_sel]

    if model_key == "dod_chain":
        new_p["use_trimmed_mean"] = st.checkbox(
            "Drop min/max outlier pairs (trimmed mean)",
            value=current_p.get("use_trimmed_mean", True), key="dod_trimmed",
        )

    if model_key == "ema_baseline":
        new_p["use_ewma"] = st.checkbox(
            "Use EWMA weighting for weekday multipliers",
            value=current_p.get("use_ewma", True), key="ema_use_ewma",
        )
        new_p["ema_span"] = st.slider(
            "EMA span (days)", 7, 30,
            value=int(current_p.get("ema_span", 14)), key="ema_span",
        )
        if new_p["use_ewma"]:
            new_p["ewma_halflife"] = st.slider(
                "EWMA half-life (weeks)", 1, 12,
                value=int(current_p.get("ewma_halflife", 4)), key="ema_halflife",
            )

    if model_key == "trend_dow":
        new_p["trend_lookback_weeks"] = st.slider(
            "Trend detection window (weeks)", 2, 8,
            value=int(current_p.get("trend_lookback_weeks", 4)), key="trend_lw",
        )

    if model_key == "ensemble":
        st.info("Ensemble is the median of all five other models. No parameters to tune.")

    st.session_state.local_params[model_key] = {
        k: v for k, v in new_p.items() if v != saved_p.get(k)
    }
    if st.session_state.local_params.get(model_key):
        st.caption("_Unsaved changes — chart reflects current values._")

    col_save, col_reset = st.columns(2)
    with col_save:
        if st.button("Save Settings", use_container_width=True, key="btn_save_settings"):
            st.session_state.model_settings[model_key] = new_p
            st.session_state.local_params[model_key]   = {}
            st.success("Settings saved for this session.")
            st.rerun()
    with col_reset:
        if st.button("Reset to Defaults", use_container_width=True, key="btn_reset"):
            st.session_state.model_settings.pop(model_key, None)
            st.session_state.local_params[model_key] = {}
            st.rerun()

    st.divider()

    # Chart
    if has_data:
        proj_fn_map = {
            "dod_chain":    project_dod_chain,
            "adaptive_dow": project_adaptive_dow,
            "same_dow":     project_same_dow,
            "ema_baseline": project_ema_baseline,
            "trend_dow":    project_trend_dow,
        }
        proj_df = all_proj["ensemble"] if model_key == "ensemble" \
                  else proj_fn_map[model_key](df, new_p, today)

        st.plotly_chart(make_chart(proj_df, model_name), use_container_width=True)

        total_proj = projected_total(proj_df, actual_mtd)
        c1, c2 = st.columns(2)
        with c1: st.metric("MTD Actual",            f"${actual_mtd:,.0f}")
        with c2: st.metric("Projected Month Total", f"${total_proj:,.0f}")

        with st.expander("Day-of-Week Breakdown", expanded=False):
            dow_rows = []
            for d in DOW_SHORT:
                sub = proj_df[proj_df["date"].dt.strftime("%a") == d]
                act = sub[sub["type"] == "actual"]["spend"].sum()
                fut = sub[sub["type"] == "projected"]["spend"].mean()
                dow_rows.append({
                    "Day":               d,
                    "Actual (avg $)":    f"${act:,.0f}" if act > 0         else "—",
                    "Projected (avg $)": f"${fut:,.0f}" if not np.isnan(fut) else "—",
                })
            st.dataframe(pd.DataFrame(dow_rows), use_container_width=True, hide_index=True)

        with st.expander("Download Projection", expanded=False):
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
        st.info("No spend data loaded yet. Upload a CSV via the sidebar.")
