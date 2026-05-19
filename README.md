# Aurora - Space Weather Monitor

A real-time space weather monitoring app that pulls live data from NOAA's Space Weather Prediction Center, generates an AI-written briefing and severity score via Gemini, and stores everything in a local SQLite database.

---

## Features

- **Live NOAA data** — Kp index (geomagnetic activity), solar wind speed/density, and solar flare detection from GOES X-ray flux
- **AI briefings** — Gemini summarizes each report in plain English and assigns a 1–10 severity score
- **Status classification** — Quiet / Unsettled / Storm / Severe based on severity score
- **SQLite storage** — every report, flare event, and reading is persisted locally
- **CLI** — run reports on demand from the terminal

---

## Project Structure

```
Aurora/
├── aurora.py         # CLI — fetches NOAA data, calls Gemini, saves to DB
├── db.py             # SQLite database layer
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Prerequisites

- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/)

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/JayceJimmerson/Aurora
cd aurora

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
cp .env.example .env
# Edit .env and add your Gemini API key (GEMINI_API_KEY)
```

---

## Usage

### Generate a report (CLI)

```bash
python aurora.py              # pulls last 1 day of data
python aurora.py --days 3     # pulls last 3 days
python aurora.py --days 7     # pulls last 7 days (NOAA max)
```

Output example:
```
============================================================
  REPORT #1 — 2026-04-07 22:13 UTC
  Status: Quiet  |  Severity: 2/10
  Max Kp: 3.67   |  Avg Wind: 513.4 km/s
  Flares — X:0 M:1 C:21

  Briefing:
  Space weather conditions over the past three days have remained
  mostly quiet to unsettled...
============================================================
```

---

## Data Sources

All data is fetched from [NOAA SWPC](https://www.swpc.noaa.gov/) public endpoints — no API key required.

| Data | Endpoint |
|---|---|
| Kp index (3-hourly) | `products/noaa-planetary-k-index.json` |
| Solar wind (propagated) | `products/geospace/propagated-solar-wind.json` |
| GOES X-ray flux (7-day) | `json/goes/primary/xrays-7-day.json` |

Solar flare events are detected from the raw X-ray flux time series: contiguous periods where flux exceeds the C-class threshold (1×10⁻⁶ W/m²) are grouped into events and classified at their peak.

---

## Severity Scale

| Score | Status | Meaning |
|---|---|---|
| 1–3 | Quiet | Minimal geomagnetic activity |
| 4–5 | Unsettled | Elevated Kp, possible minor storm |
| 6–7 | Storm | G2–G3 geomagnetic storm |
| 8–10 | Severe | G4–G5 extreme storm event |

---

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key (required) |
