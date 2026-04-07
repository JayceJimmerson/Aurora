import json
from flask import Flask, render_template, abort

import db

app = Flask(__name__)
db.init_db()


def _status_class(status):
    return {
        'Quiet':     'status-quiet',
        'Unsettled': 'status-unsettled',
        'Storm':     'status-storm',
        'Severe':    'status-severe',
    }.get(status, 'status-quiet')


@app.route('/')
def dashboard():
    reports = db.get_reports(limit=50)

    # Pull Kp chart data from the most recent report
    chart_labels = []
    chart_values = []
    latest_id = db.get_latest_report_id()
    if latest_id:
        kp_data = db.get_report_kp(latest_id)
        # Show at most 80 points for readability
        step = max(1, len(kp_data) // 80)
        kp_data = kp_data[::step]
        chart_labels = [r['time_tag'] for r in kp_data]
        chart_values = [r['kp_index'] for r in kp_data]

    latest = reports[0] if reports else None

    return render_template(
        'dashboard.html',
        reports=reports,
        latest=latest,
        status_class=_status_class(latest['status']) if latest else 'status-quiet',
        chart_labels=json.dumps(chart_labels),
        chart_values=json.dumps(chart_values),
    )


@app.route('/report/<int:report_id>')
def report_detail(report_id):
    report = db.get_report(report_id)
    if not report:
        abort(404)

    flares = db.get_report_flares(report_id)
    kp     = db.get_report_kp(report_id)
    wind   = db.get_report_wind(report_id)

    # Summary stats for the detail page
    kp_vals    = [r['kp_index'] for r in kp if r['kp_index'] is not None]
    speeds     = [r['speed']    for r in wind if r['speed']   is not None]
    densities  = [r['density']  for r in wind if r['density'] is not None]

    stats = {
        'kp_max':     round(max(kp_vals), 2)  if kp_vals    else 'N/A',
        'kp_avg':     round(sum(kp_vals) / len(kp_vals), 2) if kp_vals else 'N/A',
        'wind_max':   round(max(speeds), 1)   if speeds     else 'N/A',
        'wind_avg':   round(sum(speeds) / len(speeds), 1)   if speeds  else 'N/A',
        'density_avg': round(sum(densities) / len(densities), 2) if densities else 'N/A',
    }

    # Chart for this report's Kp
    step = max(1, len(kp) // 80)
    kp_sample = kp[::step]
    chart_labels = json.dumps([r['time_tag'] for r in kp_sample])
    chart_values = json.dumps([r['kp_index'] for r in kp_sample])

    # Wind chart (speed)
    wind_step = max(1, len(wind) // 80)
    wind_sample = wind[::wind_step]
    wind_labels = json.dumps([r['time_tag'] for r in wind_sample])
    wind_speeds  = json.dumps([r['speed']   for r in wind_sample])

    return render_template(
        'report.html',
        report=report,
        flares=flares,
        stats=stats,
        status_class=_status_class(report['status']),
        chart_labels=chart_labels,
        chart_values=chart_values,
        wind_labels=wind_labels,
        wind_speeds=wind_speeds,
    )


if __name__ == '__main__':
    app.run(debug=True)
