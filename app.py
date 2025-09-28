# ui/app.py
# Eloqua Intelligence Copilot — Streamlit App

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, timedelta

st.set_page_config(page_title="Eloqua Intelligence Copilot", layout="wide")

# Repo-relative paths
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "ingest" / "example_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def ensure_example_data():
    """Create synthetic Eloqua-like data if CSVs are missing."""
    emails_csv = DATA_DIR / "emails_by_segment_daily.csv"
    segwin_csv = DATA_DIR / "segment_engagement_windows.csv"
    if emails_csv.exists() and segwin_csv.exists():
        return

    today = date(2025, 9, 28)
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    segments = [
        {"segment_id": "MPE", "segment_name": "Owner Relations – East"},
        {"segment_id": "MPW", "segment_name": "Owner Relations – West"},
        {"segment_id": "CORP", "segment_name": "Corporate HQ"},
    ]

    rows = []
    for dt in dates:
        for s in segments:
            sends = np.random.randint(600, 1200)
            opens = int(sends * np.random.uniform(0.25, 0.4))
            clicks = int(opens * np.random.uniform(0.07, 0.13))
            unsubs = np.random.randint(0, max(1, sends // 1500))
            rows.append({
                "date": dt.isoformat(),
                "segment_id": s["segment_id"],
                "segment_name": s["segment_name"],
                "sends": sends,
                "opens": opens,
                "clicks": clicks,
                "unsubs": unsubs,
                "spam_complaints": 0,
                "unique_contacts_reached": int(sends * np.random.uniform(0.7, 0.95)),
            })
    df = pd.DataFrame(rows)
    df.to_csv(emails_csv, index=False)

    dfr = df.copy()
    dfr["date"] = pd.to_datetime(dfr["date"])
    dfr["EPC_7d"] = dfr["sends"] / dfr["unique_contacts_reached"].replace(0, np.nan)
    dfr["ctor_7d"] = dfr["clicks"] / dfr["opens"].replace(0, np.nan)
    dfr["unsub_rate_7d"] = dfr["unsubs"] / dfr["sends"].replace(0, np.nan)
    dfr["oversaturation_flag"] = dfr["EPC_7d"] > 4
    dfr["fatigue_score"] = (dfr["EPC_7d"].fillna(0) / 5.0).clip(0,1)
    dfr.to_csv(segwin_csv, index=False)

# Make sure data exists
ensure_example_data()

# Load data
df = pd.read_csv(DATA_DIR / "emails_by_segment_daily.csv", parse_dates=["date"])
df_roll = pd.read_csv(DATA_DIR / "segment_engagement_windows.csv", parse_dates=["date"])

st.title("Eloqua Intelligence Copilot")
st.caption("Executive-Ready Insights + Fatigue & Frequency Optimizer")

# KPI cards
end = df["date"].max()
start = end - pd.Timedelta(days=6)
week = df[(df["date"] >= start) & (df["date"] <= end)]
last_week = df[(df["date"] >= start - pd.Timedelta(days=7)) & (df["date"] <= end - pd.Timedelta(days=7))]

def kpi(label, current, previous=None, pct=False):
    delta = None
    if previous is not None and previous != 0:
        delta = (current - previous) / previous * 100.0
    st.metric(label, f"{current:.2%}" if pct else f"{int(current)}",
              None if delta is None else f"{delta:+.1f}%")

c1, c2, c3, c4 = st.columns(4)
with c1: kpi("Sends (7d)", week["sends"].sum(), last_week["sends"].sum(), pct=False)
with c2: kpi("Open Rate", week["opens"].sum()/max(1,week["sends"].sum()),
             last_week["opens"].sum()/max(1,last_week["sends"].sum()), pct=True)
with c3: kpi("CTR", week["clicks"].sum()/max(1,week["sends"].sum()),
             last_week["clicks"].sum()/max(1,last_week["sends"].sum()), pct=True)
with c4: kpi("CTOR", week["clicks"].sum()/max(1,week["opens"].sum()),
             last_week["clicks"].sum()/max(1,last_week["opens"].sum()), pct=True)

# Segment table
st.subheader("Segments — This Week")
seg = week.groupby("segment_name").agg(sends=("sends","sum"),
                                       opens=("opens","sum"),
                                       clicks=("clicks","sum"),
                                       unsubs=("unsubs","sum"))
seg["open_rate"] = seg["opens"]/seg["sends"]
seg["ctr"] = seg["clicks"]/seg["sends"]
seg["ctor"] = seg["clicks"]/seg["opens"].clip(lower=1)
st.dataframe(seg.reset_index())

# Fatigue alerts
st.subheader("Fatigue Alerts — Latest Day")
recent = df_roll[df_roll["date"]==df_roll["date"].max()]
alerts = recent[(recent["oversaturation_flag"]) | (recent["fatigue_score"]>0.6)].copy()
if alerts.empty:
    st.success("No fatigue alerts today. 👍")
else:
    cols = [c for c in ["date","segment_id","EPC_7d","ctor_7d",
                        "unsub_rate_7d","fatigue_score","oversaturation_flag"] if c in alerts.columns]
    st.dataframe(alerts[cols])

# Weekly brief
st.divider()
st.subheader("Auto-Generated Weekly Brief (Markdown)")
top_seg = seg["ctor"].idxmax()
lag_seg = seg["ctor"].idxmin()
brief = f"""
# Eloqua Performance Brief ({str(start.date())} to {str(end.date())})

**Headlines**
- Overall CTOR: {week["clicks"].sum()/max(1,week["opens"].sum()):.2%}
  (Δ vs last week: {((week["clicks"].sum()/max(1,week["opens"].sum())) - (last_week["clicks"].sum()/max(1,last_week["opens"].sum()))):+.2%})
- Top segment: **{top_seg}** (CTOR {seg.loc[top_seg,"ctor"]:.2%})
- Lagging segment: **{lag_seg}** (CTOR {seg.loc[lag_seg,"ctor"]:.2%})

**Fatigue & Risk**
- Segments with oversaturation or high fatigue score are flagged above.
  Throttle where EPC-7d > 4 and CTOR-7d breaks below baseline.

**Next Best Tests**
- Subject: Verb-led, 5–7 words vs urgency phrase
- CTA: “Review & Confirm” vs “Confirm Now”
- Send-time: 09:30 vs 13:00
"""
st.code(brief, language="markdown")
