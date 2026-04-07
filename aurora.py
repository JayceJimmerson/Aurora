#!/usr/bin/env python3
"""
Aurora - Space Weather Monitor
CLI entry point. Fetches real-time data from NOAA SWPC and generates
an AI briefing via Claude Haiku.

Usage:
    python sentinel.py
    python sentinel.py --days 3
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

import requests
import anthropic
from dotenv import load_dotenv

import db

load_dotenv()

NOAA_BASE = "https://services.swpc.noaa.gov"
REQUEST_TIMEOUT = 20


# ---------------------------------------------------------------------------
# NOAA data fetchers
# ---------------------------------------------------------------------------

def _parse_dt(s):
    """Parse NOAA datetime strings which come in a few formats."""
    s = s.strip()
    for fmt in ('%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Unrecognised datetime format: {s!r}")


def fetch_kp_index(days):
    """Fetch 3-hourly Kp index from NOAA. Returns list of dicts."""
    url = f"{NOAA_BASE}/products/noaa-planetary-k-index.json"
    print(f"  Fetching Kp index from NOAA...")
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    readings = []
    for row in data:
        try:
            # API returns list of dicts: {'time_tag': '...', 'Kp': 2.0, ...}
            dt = _parse_dt(row['time_tag'])
            kp_val = row.get('Kp')
            if kp_val is None:
                continue
            if dt >= cutoff:
                readings.append({'time_tag': row['time_tag'], 'kp_index': float(kp_val)})
        except (ValueError, KeyError, TypeError):
            continue

    print(f"    Got {len(readings)} Kp readings")
    return readings


def _classify_flux(flux):
    """Return flare class letter and formatted class string for a given X-ray flux (W/m²)."""
    if flux >= 1e-4:
        letter = 'X'
        num = flux / 1e-4
    elif flux >= 1e-5:
        letter = 'M'
        num = flux / 1e-5
    elif flux >= 1e-6:
        letter = 'C'
        num = flux / 1e-6
    elif flux >= 1e-7:
        letter = 'B'
        num = flux / 1e-7
    else:
        letter = 'A'
        num = flux / 1e-8
    return letter, f"{letter}{num:.1f}"


def fetch_solar_flares(days):
    """Detect solar flare events from GOES X-ray flux data (up to 7 days). Returns list of dicts."""
    url = f"{NOAA_BASE}/json/goes/primary/xrays-7-day.json"
    print(f"  Fetching X-ray flux data from NOAA GOES...")
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    # Filter to the long-wavelength channel (0.1-0.8nm) and requested days
    cutoff = datetime.now(timezone.utc) - timedelta(days=min(days, 7))
    long_wave = [
        r for r in data
        if r.get('energy') == '0.1-0.8nm'
        and r.get('flux') is not None
        and _parse_dt(r['time_tag']) >= cutoff
    ]

    # Detect flare events: contiguous runs above C-class threshold (1e-6 W/m²)
    C_THRESHOLD = 1e-6
    flares = []
    in_flare = False
    begin_time = peak_time = end_time = None
    peak_flux = 0.0

    for reading in long_wave:
        flux = reading.get('flux') or 0.0
        tag  = reading['time_tag']

        if not in_flare and flux >= C_THRESHOLD:
            in_flare   = True
            begin_time = tag
            peak_time  = tag
            peak_flux  = flux
        elif in_flare:
            if flux > peak_flux:
                peak_flux = flux
                peak_time = tag
            if flux < C_THRESHOLD:
                end_time = tag
                _, cls = _classify_flux(peak_flux)
                flares.append({
                    'begin_time':  begin_time,
                    'peak_time':   peak_time,
                    'end_time':    end_time,
                    'flare_class': cls,
                    'max_flux':    peak_flux,
                })
                in_flare = False
                peak_flux = 0.0

    # Close any still-open flare at end of data
    if in_flare:
        _, cls = _classify_flux(peak_flux)
        flares.append({
            'begin_time':  begin_time,
            'peak_time':   peak_time,
            'end_time':    long_wave[-1]['time_tag'] if long_wave else '',
            'flare_class': cls,
            'max_flux':    peak_flux,
        })

    print(f"    Detected {len(flares)} flare events (C-class and above)")
    return flares


def fetch_solar_wind(days):
    """Fetch propagated solar wind (speed, density, temperature) from NOAA. Returns list of dicts."""
    url = f"{NOAA_BASE}/products/geospace/propagated-solar-wind.json"
    print(f"  Fetching solar wind data from NOAA...")
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    # First row is a header list; skip it
    if data and isinstance(data[0], list) and data[0][0] == 'time_tag':
        data = data[1:]

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    def _safe(v):
        if v in (None, 'null', '', '-9999.9', '-9999') or v in (-9999.9, -9999):
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    readings = []
    for row in data:
        try:
            dt = _parse_dt(row[0])
            if dt < cutoff:
                continue
            readings.append({
                'time_tag':    row[0],
                'speed':       _safe(row[1]),
                'density':     _safe(row[2]),
                'temperature': _safe(row[3]),
            })
        except (ValueError, IndexError, TypeError):
            continue

    # Downsample to ~144 readings (~1 per 10 min for 1 day) to keep DB tidy
    if len(readings) > 144:
        step = max(1, len(readings) // 144)
        readings = readings[::step]

    print(f"    Got {len(readings)} solar wind readings (downsampled)")
    return readings


# ---------------------------------------------------------------------------
# Summary statistics helpers
# ---------------------------------------------------------------------------

def summarise_kp(readings):
    vals = [r['kp_index'] for r in readings if r['kp_index'] is not None]
    if not vals:
        return {'max': 0, 'avg': 0, 'current': 0}
    return {'max': max(vals), 'avg': round(sum(vals) / len(vals), 2), 'current': vals[-1]}


def summarise_wind(readings):
    speeds  = [r['speed']   for r in readings if r['speed']   is not None]
    densities = [r['density'] for r in readings if r['density'] is not None]
    if not speeds:
        return {'avg_speed': 0, 'max_speed': 0, 'avg_density': 0}
    return {
        'avg_speed':   round(sum(speeds) / len(speeds), 1),
        'max_speed':   round(max(speeds), 1),
        'avg_density': round(sum(densities) / len(densities), 2) if densities else 0,
    }


def classify_flares(flares):
    classes = {'X': 0, 'M': 0, 'C': 0, 'B': 0, 'A': 0}
    for f in flares:
        letter = (f['flare_class'] or 'U')[0].upper()
        if letter in classes:
            classes[letter] += 1
    return classes


# ---------------------------------------------------------------------------
# Claude Haiku briefing
# ---------------------------------------------------------------------------

def generate_briefing(days, kp_stats, wind_stats, flare_counts, flares):
    client = anthropic.Anthropic()

    notable_flares = [f for f in flares if f['flare_class'] and f['flare_class'][0].upper() in ('X', 'M')]
    flare_lines = '\n'.join(
        f"  - {f['flare_class']} at {f['begin_time']} (peak: {f['peak_time']})"
        for f in notable_flares[:10]
    ) or '  None significant'

    prompt = f"""You are a space weather analyst. Based on the data below from the past {days} day(s), write:
1. A plain-English briefing (3–5 sentences, suitable for a general audience) describing current space weather conditions.
2. A severity score from 1 to 10 (1 = completely quiet, 10 = extreme storm event).

Space weather data summary:
- Observation window: last {days} day(s)
- Kp index — max: {kp_stats['max']}, average: {kp_stats['avg']}, most recent: {kp_stats['current']}
- Solar wind — avg speed: {wind_stats['avg_speed']} km/s, max speed: {wind_stats['max_speed']} km/s, avg density: {wind_stats['avg_density']} p/cm³
- Solar flares — X-class: {flare_counts['X']}, M-class: {flare_counts['M']}, C-class: {flare_counts['C']}
- Notable flare events:
{flare_lines}

Kp scale reference: 0–1 quiet, 2–3 unsettled, 4 active, 5 minor storm (G1), 6 moderate storm (G2), 7 strong storm (G3), 8 severe storm (G4), 9 extreme storm (G5).

Respond in this exact JSON format (no markdown, no extra text):
{{
  "briefing": "<your briefing here>",
  "severity_score": <integer 1-10>
}}"""

    print("  Generating AI briefing via Claude Haiku...")
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text.strip()
    # Strip markdown code fences if model wrapped it anyway
    if text.startswith('```'):
        text = text.split('```')[1]
        if text.startswith('json'):
            text = text[4:]
    text = text.strip()

    result = json.loads(text)
    briefing = result['briefing']
    score = max(1, min(10, int(result['severity_score'])))
    return briefing, score


# ---------------------------------------------------------------------------
# Status label
# ---------------------------------------------------------------------------

def score_to_status(score):
    if score <= 3:
        return 'Quiet'
    elif score <= 5:
        return 'Unsettled'
    elif score <= 7:
        return 'Storm'
    else:
        return 'Severe'


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(days):
    print(f"\n Aurora Space Weather Monitor")
    print(f" Fetching data for the past {days} day(s)...\n")

    db.init_db()

    try:
        kp_readings  = fetch_kp_index(days)
        flares       = fetch_solar_flares(days)
        wind_readings = fetch_solar_wind(days)
    except requests.RequestException as e:
        print(f"\nError fetching data from NOAA: {e}", file=sys.stderr)
        sys.exit(1)

    kp_stats    = summarise_kp(kp_readings)
    wind_stats  = summarise_wind(wind_readings)
    flare_counts = classify_flares(flares)

    try:
        briefing, score = generate_briefing(days, kp_stats, wind_stats, flare_counts, flares)
    except (anthropic.APIError, json.JSONDecodeError, KeyError) as e:
        print(f"\nError generating briefing: {e}", file=sys.stderr)
        sys.exit(1)

    status = score_to_status(score)

    print(f"\n  Saving report to database...")
    report_id = db.save_report(days, score, status, briefing)
    db.save_kp_readings(report_id, kp_readings)
    db.save_flares(report_id, flares)
    db.save_solar_wind(report_id, wind_readings)

    print(f"\n{'='*60}")
    print(f"  REPORT #{report_id} — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Status: {status}  |  Severity: {score}/10")
    print(f"  Max Kp: {kp_stats['max']}  |  Avg Wind: {wind_stats['avg_speed']} km/s")
    print(f"  Flares — X:{flare_counts['X']} M:{flare_counts['M']} C:{flare_counts['C']}")
    print(f"\n  Briefing:\n  {briefing}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Aurora — Space Weather Monitor CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--days', type=int, default=1, metavar='N',
        help='Number of days of history to pull (default: 1, max useful: 7)'
    )
    args = parser.parse_args()

    if args.days < 1:
        parser.error("--days must be at least 1")
    if args.days > 30:
        print("Warning: NOAA endpoints typically only hold 1–7 days of real-time data; "
              "limiting to 7 days for flare events.", file=sys.stderr)

    run(args.days)


if __name__ == '__main__':
    main()
