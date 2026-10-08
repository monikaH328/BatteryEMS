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
            energy_flow_json TEXT NOT NULL DEFAULT '{}',
            equivalent_full_cycles REAL NOT NULL DEFAULT 0.0
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
            "equivalent_full_cycles":"REAL NOT NULL DEFAULT 0.0",
            # --- cycle testing foundation (additive; old rows -> cycle_id=NULL, test_state='IDLE') ---
            "cycle_id":"INTEGER DEFAULT NULL",
            "test_state":"TEXT NOT NULL DEFAULT 'IDLE'",
        }
        for col, typ in additions.items():
            if col not in cols: _connection.execute(f"ALTER TABLE battery_readings ADD COLUMN {col} {typ}")

        # New, separate table for cycle metadata. Does not touch battery_readings' existing rows.
        _connection.execute("""CREATE TABLE IF NOT EXISTS cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_number INTEGER NOT NULL,
            test_state TEXT NOT NULL DEFAULT 'CHARGE',
            status TEXT NOT NULL DEFAULT 'RUNNING',
            start_time TEXT NOT NULL,
            end_time TEXT
        )""")
        _connection.commit()
    return _connection

def insert_snapshot(timestamp, soc_percent, soh_percent, cell_voltages, pack_voltage,
                    pack_current, temperature, battery_status, grid_status,
                    operating_mode, faults, balancing_cells, ems_decision, energy_flow,
                    equivalent_full_cycles=0.0, cycle_id=None, test_state="IDLE"):
    init_database()
    with _db_lock:
        _connection.execute("""INSERT INTO battery_readings
        (timestamp,soc_percent,soh_percent,cell_voltages_json,pack_voltage,pack_current,
         temperature,battery_status,grid_status,operating_mode,balancing_cells_json,
         faults_json,ems_decision_json,energy_flow_json,equivalent_full_cycles,
         cycle_id,test_state)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (timestamp,float(soc_percent),float(soh_percent),json.dumps(cell_voltages),
         float(pack_voltage),float(pack_current),float(temperature),str(battery_status),
         str(grid_status),str(operating_mode),json.dumps(balancing_cells),
         json.dumps(faults),json.dumps(ems_decision),json.dumps(energy_flow),
         float(equivalent_full_cycles),
         int(cycle_id) if cycle_id is not None else None, str(test_state)))
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
        if limit is None:
            rows=_connection.execute("SELECT * FROM battery_readings ORDER BY id DESC").fetchall()
        else:
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


# --------------------------------------------------------------------
# CYCLE TESTING (additive; does not touch existing readings/functions)
# --------------------------------------------------------------------
def create_cycle(test_state="CHARGE"):
    """Creates a new cycle row and returns it as a dict. Does NOT control
    any charger/load/relay -- this only records that a cycle test started."""
    init_database()
    with _db_lock:
        row = _connection.execute("SELECT COALESCE(MAX(cycle_number),0) AS m FROM cycles").fetchone()
        cycle_number = int(row["m"]) + 1
        start_time = get_db_timestamp()
        cur = _connection.execute(
            "INSERT INTO cycles (cycle_number, test_state, status, start_time) VALUES (?,?,?,?)",
            (cycle_number, str(test_state), "RUNNING", start_time),
        )
        _connection.commit()
        cycle_id = cur.lastrowid
        return dict(_connection.execute("SELECT * FROM cycles WHERE id=?", (cycle_id,)).fetchone())

def stop_cycle(cycle_id):
    """Marks a cycle as STOPPED with an end_time. No hardware side effects."""
    init_database()
    with _db_lock:
        end_time = get_db_timestamp()
        _connection.execute(
            "UPDATE cycles SET status='STOPPED', end_time=? WHERE id=? AND status='RUNNING'",
            (end_time, int(cycle_id)),
        )
        _connection.commit()
        row = _connection.execute("SELECT * FROM cycles WHERE id=?", (int(cycle_id),)).fetchone()
        return dict(row) if row else None

def get_cycles():
    init_database()
    with _db_lock:
        rows = _connection.execute("SELECT * FROM cycles ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

def get_cycle(cycle_id):
    init_database()
    with _db_lock:
        row = _connection.execute("SELECT * FROM cycles WHERE id=?", (int(cycle_id),)).fetchone()
    return dict(row) if row else None

def get_readings_for_cycle(cycle_id):
    init_database()
    with _db_lock:
        rows = _connection.execute(
            "SELECT * FROM battery_readings WHERE cycle_id=? ORDER BY id ASC", (int(cycle_id),)
        ).fetchall()
    return [_decode(r) for r in rows]
