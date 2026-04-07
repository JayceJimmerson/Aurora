import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aurora.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT    NOT NULL,
            days_requested INTEGER NOT NULL,
            severity_score REAL NOT NULL,
            status      TEXT    NOT NULL,
            briefing    TEXT    NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS solar_flares (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id   INTEGER NOT NULL,
            begin_time  TEXT,
            peak_time   TEXT,
            end_time    TEXT,
            flare_class TEXT,
            max_flux    REAL,
            FOREIGN KEY (report_id) REFERENCES reports(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS kp_readings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id   INTEGER NOT NULL,
            time_tag    TEXT    NOT NULL,
            kp_index    REAL    NOT NULL,
            FOREIGN KEY (report_id) REFERENCES reports(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS solar_wind (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id   INTEGER NOT NULL,
            time_tag    TEXT    NOT NULL,
            speed       REAL,
            density     REAL,
            temperature REAL,
            FOREIGN KEY (report_id) REFERENCES reports(id)
        )
    ''')

    conn.commit()
    conn.close()


def save_report(days, severity_score, status, briefing):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        'INSERT INTO reports (created_at, days_requested, severity_score, status, briefing) VALUES (?, ?, ?, ?, ?)',
        (datetime.utcnow().isoformat(timespec='seconds'), days, severity_score, status, briefing)
    )
    report_id = c.lastrowid
    conn.commit()
    conn.close()
    return report_id


def save_flares(report_id, flares):
    if not flares:
        return
    conn = get_connection()
    c = conn.cursor()
    c.executemany(
        'INSERT INTO solar_flares (report_id, begin_time, peak_time, end_time, flare_class, max_flux) VALUES (?,?,?,?,?,?)',
        [(report_id, f['begin_time'], f['peak_time'], f['end_time'], f['flare_class'], f['max_flux']) for f in flares]
    )
    conn.commit()
    conn.close()


def save_kp_readings(report_id, readings):
    if not readings:
        return
    conn = get_connection()
    c = conn.cursor()
    c.executemany(
        'INSERT INTO kp_readings (report_id, time_tag, kp_index) VALUES (?,?,?)',
        [(report_id, r['time_tag'], r['kp_index']) for r in readings]
    )
    conn.commit()
    conn.close()


def save_solar_wind(report_id, readings):
    if not readings:
        return
    conn = get_connection()
    c = conn.cursor()
    c.executemany(
        'INSERT INTO solar_wind (report_id, time_tag, speed, density, temperature) VALUES (?,?,?,?,?)',
        [(report_id, r['time_tag'], r['speed'], r['density'], r['temperature']) for r in readings]
    )
    conn.commit()
    conn.close()


def get_reports(limit=50):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM reports ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_report(report_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_report_flares(report_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM solar_flares WHERE report_id = ? ORDER BY begin_time', (report_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_report_kp(report_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM kp_readings WHERE report_id = ? ORDER BY time_tag', (report_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_report_wind(report_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM solar_wind WHERE report_id = ? ORDER BY time_tag', (report_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_report_id():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id FROM reports ORDER BY created_at DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    return row['id'] if row else None
