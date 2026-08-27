"""SQLite storage with backward-compatible migration from the prototype schema."""
from __future__ import annotations
import json, os, sqlite3, threading
from datetime import datetime
import config

_connection = None
_db_lock = threading.RLock()

def init_database():
    global _connection
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
    if _connection is None:
        _connection = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
    with _db_lock:
        _connection.execute("""CREATE TABLE IF NOT EXISTS battery_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            soc_percent REAL NOT NULL,
            pack_voltage REAL NOT NULL,
            pack_current REAL NOT NULL,
            temperature REAL NOT NULL,
            battery_status TEXT NOT NULL,
            grid_status TEXT NOT NULL,
            soh_percent REAL NOT NULL DEFAULT 100.0,
            cell_voltages_json TEXT NOT NULL DEFAULT '[]',
            operating_mode TEXT NOT NULL DEFAULT 'idle',
            balancing_cells_json TEXT NOT NULL DEFAULT '[]',
            faults_json TEXT NOT NULL DEFAULT '[]',
            ems_decision_json TEXT NOT NULL DEFAULT '{}',
            energy_flow_json TEXT NOT NULL DEFAULT '{}'
        )""")
        cols={r[1] for r in _connection.execute("PRAGMA table_info(battery_readings)")}
        additions={
            "soh_percent":"REAL NOT NULL DEFAULT 100.0",
            "cell_voltages_json":"TEXT NOT NULL DEFAULT '[]'",
            "operating_mode":"TEXT NOT NULL DEFAULT 'idle'",
            "balancing_cells_json":"TEXT NOT NULL DEFAULT '[]'",
            "faults_json":"TEXT NOT NULL DEFAULT '[]'",
            "ems_decision_json":"TEXT NOT NULL DEFAULT '{}'",
            "energy_flow_json":"TEXT NOT NULL DEFAULT '{}'",
        }
        for col, typ in additions.items():
            if col not in cols: _connection.execute(f"ALTER TABLE battery_readings ADD COLUMN {col} {typ}")
        _connection.commit()
    return _connection

def insert_snapshot(timestamp, soc_percent, soh_percent, cell_voltages, pack_voltage,
                    pack_current, temperature, battery_status, grid_status,
                    operating_mode, faults, balancing_cells, ems_decision, energy_flow):
    init_database()
    with _db_lock:
        _connection.execute("""INSERT INTO battery_readings
        (timestamp,soc_percent,soh_percent,cell_voltages_json,pack_voltage,pack_current,
         temperature,battery_status,grid_status,operating_mode,balancing_cells_json,
         faults_json,ems_decision_json,energy_flow_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (timestamp,float(soc_percent),float(soh_percent),json.dumps(cell_voltages),
         float(pack_voltage),float(pack_current),float(temperature),str(battery_status),
         str(grid_status),str(operating_mode),json.dumps(balancing_cells),
         json.dumps(faults),json.dumps(ems_decision),json.dumps(energy_flow)))
        _connection.commit()

def insert_reading(timestamp,soc_percent,pack_voltage,pack_current,temperature,battery_status,grid_status):
    insert_snapshot(timestamp,soc_percent,100.0,[],pack_voltage,pack_current,temperature,battery_status,grid_status,"idle",[],[],{},{})

def _decode(row):
    d=dict(row)
    for key in ("cell_voltages_json","balancing_cells_json","faults_json","ems_decision_json","energy_flow_json"):
        target=key.replace("_json","")
        try: d[target]=json.loads(d.pop(key))
        except Exception: d[target]=[] if "cells" in key or "faults" in key else {}
    return d

def get_recent_readings(limit=100):
    init_database()
    with _db_lock:
        rows=_connection.execute("SELECT * FROM battery_readings ORDER BY id DESC LIMIT ?",(int(limit),)).fetchall()
    return [_decode(r) for r in reversed(rows)]

def get_readings_between(start,end,limit=None):
    init_database(); q="SELECT * FROM battery_readings WHERE timestamp BETWEEN ? AND ? ORDER BY id DESC"; p=[str(start),str(end)]
    if limit is not None: q+=" LIMIT ?"; p.append(int(limit))
    with _db_lock: rows=_connection.execute(q,p).fetchall()
    return [_decode(r) for r in reversed(rows)]

def get_latest_soc():
    init_database()
    with _db_lock:
        row=_connection.execute("SELECT soc_percent FROM battery_readings ORDER BY id DESC LIMIT 1").fetchone()
    return row["soc_percent"] if row else None

def get_statistics():
    init_database()
    with _db_lock:
        row=_connection.execute("""SELECT COUNT(*) total_readings,AVG(soc_percent) avg_soc,
        MIN(soc_percent) min_soc,MAX(soc_percent) max_soc,AVG(soh_percent) avg_soh,
        AVG(pack_voltage) avg_voltage,AVG(pack_current) avg_current,AVG(temperature) avg_temperature
        FROM battery_readings""").fetchone()
    return dict(row) if row else {}

def get_fault_records(limit=100):
    init_database()
    with _db_lock:
        rows=_connection.execute("SELECT * FROM battery_readings WHERE battery_status='FAULT' ORDER BY id DESC LIMIT ?",(int(limit),)).fetchall()
    return [_decode(r) for r in rows]

def close_database():
    global _connection
    with _db_lock:
        if _connection: _connection.close(); _connection=None

def get_db_timestamp(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
