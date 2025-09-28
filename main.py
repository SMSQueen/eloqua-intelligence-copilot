# service/api/main.py
# Minimal FastAPI app to serve weekly brief and fatigue alerts from CSVs
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import pandas as pd
from datetime import datetime, timedelta

DATA_DIR = "/mnt/data/eloqua_intel_copilot/ingest/example_data".replace('\\', '/')

app = FastAPI(title="Eloqua Intelligence Copilot API")

def load_data():
    df = pd.read_csv(f"{DATA_DIR}/emails_by_segment_daily.csv", parse_dates=["date"])
    df_roll = pd.read_csv(f"{DATA_DIR}/segment_engagement_windows.csv", parse_dates=["date"])
    return df, df_roll

@app.get("/brief/weekly")
def weekly_brief():
    df, df_roll = load_data()
    end = df["date"].max()
    start = end - pd.Timedelta(days=6)
    week = df[(df["date"] >= start) & (df["date"] <= end)]
    last_week = df[(df["date"] >= start - pd.Timedelta(days=7)) & (df["date"] <= end - pd.Timedelta(days=7))]

    def kpi(d, m): 
        return float(d[m].sum())

    summary = {
        "window": [str(start.date()), str(end.date())],
        "sends": kpi(week, "sends"),
        "opens": kpi(week, "opens"),
        "clicks": kpi(week, "clicks"),
        "open_rate": float(week["opens"].sum() / max(1, week["sends"].sum())),
        "ctr": float(week["clicks"].sum() / max(1, week["sends"].sum())),
        "ctor": float(week["clicks"].sum() / max(1, week["opens"].sum())),
        "delta_ctor_vs_prev_week": float( (week["clicks"].sum()/max(1,week["opens"].sum())) - (last_week["clicks"].sum()/max(1,last_week["opens"].sum())) )
    }

    # Top and lagging segments by CTOR
    seg = week.groupby("segment_name").agg({"opens":"sum","clicks":"sum"})
    seg["ctor"] = seg["clicks"]/seg["opens"].clip(lower=1)
    top = seg["ctor"].idxmax()
    lag = seg["ctor"].idxmin()

    summary["top_segment"] = {"name": top, "ctor": float(seg.loc[top, "ctor"])}
    summary["lagging_segment"] = {"name": lag, "ctor": float(seg.loc[lag, "ctor"])}

    return JSONResponse(summary)

@app.get("/fatigue/alerts")
def fatigue_alerts():
    _, df_roll = load_data()
    recent = df_roll[df_roll["date"]==df_roll["date"].max()]
    alerts = recent[recent["oversaturation_flag"] | (recent["fatigue_score"]>0.6)]
    out = []
    for _, r in alerts.iterrows():
        out.append({
            "date": str(pd.to_datetime(r["date"]).date()),
            "segment_id": r["segment_id"],
            "EPC_7d": float(r["EPC_7d"]),
            "ctor_7d": float(r["ctor_7d"]),
            "fatigue_score": float(r["fatigue_score"]),
            "recommendation": "Throttle non-essential journeys for 7 days; shift FYI to portal/SMS; prioritize high-utility content."
        })
    return JSONResponse(out)
