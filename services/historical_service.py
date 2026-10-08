"""Historical telemetry service."""
import config
from database.repository import BatteryReadingRepository
class HistoricalDataService:
    def __init__(self,repository=None): self.repository=repository or BatteryReadingRepository()
    def get_history(self,limit=120,downsample=None):
        rows=self.repository.get_recent(limit)
        n=len(rows)
        if downsample and downsample > 0 and n > downsample:
            step = n / downsample
            indices = sorted(set(int(i*step) for i in range(downsample)))
            rows = [rows[i] for i in indices]
        return {"timestamps":[r["timestamp"] for r in rows],
                "soc":[float(r["soc_percent"]) for r in rows],
                "soh":[float(r.get("soh_percent",100.0)) for r in rows],
                "voltage":[float(r["pack_voltage"]) for r in rows],
                "current":[float(r["pack_current"]) for r in rows],
                "temperature":[float(r["temperature"]) for r in rows],
                "cycles":[float(r.get("equivalent_full_cycles",0.0)) for r in rows],
                "cell_voltages":[[float(r.get("cell_voltages",[])[i]) if len(r.get("cell_voltages",[]))>i else None for r in rows] for i in range(max((len(r.get("cell_voltages",[])) for r in rows), default=0))]}
    def statistics(self): return self.repository.get_statistics()
    def faults(self,limit=100): return self.repository.get_fault_records(limit)
