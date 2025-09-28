
# Eloqua Intelligence Copilot — Starter Kit

This starter kit includes synthetic Eloqua-like data, a minimal FastAPI service, a Streamlit dashboard, and SQL models for computing rolling engagement and fatigue flags.

## 📂 Project Structure
```
eloqua-intelligence-copilot/
├── ui/
│   └── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml 
├── ingest/
│   └── example_data/
│       ├── emails_by_segment_daily.csv
│       └── segment_engagement_windows.csv
├── requirements.txt
└── README.md

```

## 🚀 How to run the dashboard
1. Install dependencies:
   ```bash
   pip install streamlit fastapi uvicorn pandas numpy
   ```
2. Run the Streamlit app:
   ```bash
   streamlit run ui/app.py
   ```
3. (Optional) Run the FastAPI service:
   ```bash
   uvicorn service.api.main:app --reload
   ```

## 📊 Data Notes
- Data is synthetic, spanning 2025-09-01 to 2025-09-28 across three segments.
- The "Owner Relations – East" segment includes intentional oversaturation in the last 10 days to demonstrate fatigue flags.

## ✅ Next Steps
- Replace `ingest/example_data/*.csv` with real Eloqua extracts (Bulk API 2.0).
- Wire the API endpoints into Slack/Teams for automated briefs and fatigue alerts.
- Convert SQL to dbt models if you use a warehouse.
- Add PDF export of the executive brief for sharing with leadership.
