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
            equivalent_full_cycles=b.get("equivalent_full_cycles", 0.0),
            # additive: cycle testing foundation. Old snapshots (no keys) -> cycle_id=None, test_state='IDLE'
            cycle_id=snapshot.get("cycle_id"),
            test_state=snapshot.get("test_state", "IDLE"),
        )

    def get_recent(self, limit=100): return db.get_recent_readings(limit)
    def get_statistics(self): return db.get_statistics()
    def get_fault_records(self, limit=100): return db.get_fault_records(limit)
    def get_between(self, start, end, limit=None): return db.get_readings_between(start,end,limit)

    def get_last_equivalent_full_cycles(self):
        """Returns equivalent_full_cycles from the most recent saved reading, or 0.0 if the table is empty."""
        rows = db.get_recent_readings(1)
        if not rows:
            return 0.0
        return float(rows[-1].get("equivalent_full_cycles", 0.0))

    # --- cycle testing foundation ---
    def create_cycle(self, test_state="CHARGE"): return db.create_cycle(test_state)
    def stop_cycle(self, cycle_id): return db.stop_cycle(cycle_id)
    def list_cycles(self): return db.get_cycles()
    def get_cycle(self, cycle_id): return db.get_cycle(cycle_id)
    def get_readings_for_cycle(self, cycle_id): return db.get_readings_for_cycle(cycle_id)
