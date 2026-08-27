"""SQLite repository. The database layer is intentionally independent of UI."""
from __future__ import annotations
import json
import db

class BatteryReadingRepository:
    def save_snapshot(self, snapshot):
        b = snapshot["bms"]; e = snapshot["ems"]
        db.insert_snapshot(
            timestamp=snapshot["timestamp"],
            soc_percent=b["soc_percent"], soh_percent=b["soh_percent"],
            cell_voltages=b["cell_voltages"], pack_voltage=b["pack_voltage"],
            pack_current=b["current_a"], temperature=b["temperature_c"],
            battery_status=b["status"], grid_status="UP" if e["grid_available"] else "DOWN",
            operating_mode=e["battery_mode_commanded"],
            faults=b["faults"], balancing_cells=b["balancing_cells"],
            ems_decision=e, energy_flow=e.get("energy_flow", {}),
        )

    def get_recent(self, limit=100): return db.get_recent_readings(limit)
    def get_statistics(self): return db.get_statistics()
    def get_fault_records(self, limit=100): return db.get_fault_records(limit)
    def get_between(self, start, end, limit=None): return db.get_readings_between(start,end,limit)
