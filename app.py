# ui/app.py
# Streamlit dashboard for Eloqua Intelligence Copilot (Exec Brief + Fatigue)
import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(page_title="Eloqua Intelligence Copilot", layout="wide")

DATA_DIR = "/mnt/data/eloqua_intel_copilot/ingest/example_data".replace('\\', '/')
df = pd.read_csv(f"{DATA_DIR}/emails_by_segment_daily.csv", parse_dates=["date"])
df_roll = pd.read_csv(f"{DATA_DIR}/segment_engagement_windows.csv", parse_dates=["date"])

st.title("Eloqua Intelligence Copilot")
st.caption("Executive-Ready Insights + Fatigue & Frequency Optimizer")

end = df["date"].max()
start = end - pd.Timedelta(days=6)

week = df[(df["date"] >= start) & (df["date"] <= end)]
last_week = df[(df["date"] >= start - pd.Timedelta(days=7)) & (df["date"] <= end - pd.Timedelta(days=7))]

def kpi_row(label, current, previous=None, pct=False):
    delta = None
    if previous is not None and previous != 0:
        delta = (current - previous) / previous * 100.0
    col = st.metric(label, f"{current:.2%}" if pct else f"{int(current)}", None if delta is None else f"{delta:+.1f}%")
    return col

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_row("Sends (7d)", week["sends"].sum(), last_week["sends"].sum(), pct=False)
with c2:
    kpi_row("Open Rate", week["opens"].sum()/max(1,week["sends"].sum()),
            last_week["opens"].sum()/max(1,last_week["sends"].sum()), pct=True)
with c3:
    kpi_row("CTR", week["clicks"].sum()/max(1,week["sends"].sum()),
            last_week["clicks"].sum()/max(1,last_week["sends"].sum()), pct=True)
with c4:
    kpi_row("CTOR", week["clicks"].sum()/max(1,week["opens"].sum()),
            last_week["clicks"].sum()/max(1,last_week["opens"].sum()), pct=True)

st.subheader("Segments — This Week")
seg = week.groupby(["segment_name"]).agg(sends=("sends","sum"), opens=("opens","sum"), clicks=("clicks","sum"), unsubs=("unsubs","sum"))
seg["open_rate"] = seg["opens"]/seg["sends"]
seg["ctr"] = seg["clicks"]/seg["sends"]
seg["ctor"] = seg["clicks"]/seg["opens"].clip(lower=1)
st.dataframe(seg.reset_index())

st.subheader("Fatigue Alerts — Latest Day")
recent = df_roll[df_roll["date"]==df_roll["date"].max()]
alerts = recent[(recent["oversaturation_flag"]) | (recent["fatigue_score"]>0.6)].copy()
if alerts.empty:
    st.success("No fatigue alerts today. 👍")
else:
    alerts = alerts[["date","segment_id","EPC_7d","ctor_7d","unsub_rate_7d","fatigue_score","oversaturation_flag"]]
    st.dataframe(alerts)

st.divider()
st.subheader("Auto-Generated Weekly Brief (Markdown)")

# Simple narrative (rule-based, no external LLMs)
top_seg = seg["ctor"].idxmax()
lag_seg = seg["ctor"].idxmin()
brief = f"""
# Eloqua Performance Brief ({str(start.date())} to {str(end.date())})

**Headlines**
- Overall CTOR: {week["clicks"].sum()/max(1,week["opens"].sum()):.2%} (Δ vs last week: {((week["clicks"].sum()/max(1,week["opens"].sum())) - (last_week["clicks"].sum()/max(1,last_week["opens"].sum()))):+.2%})
- Top segment: **{top_seg}** (CTOR {seg.loc[top_seg, "ctor"]:.2%})
- Lagging segment: **{lag_seg}** (CTOR {seg.loc[lag_seg, "ctor"]:.2%})

**Fatigue & Risk**
- Segments with oversaturation or high fatigue score are flagged in the dashboard above. Throttle where EPC-7d > 4 and CTOR-7d breaks below baseline.

**Next Best Tests**
- Subject: Verb-led, 5–7 words vs urgency phrase
- CTA: “Review & Confirm” vs “Confirm Now”
- Send-time: 09:30 vs 13:00
"""
st.code(brief, language="markdown")

st.download_button("Download Weekly Brief (.md)", brief, file_name="weekly_brief.md")
