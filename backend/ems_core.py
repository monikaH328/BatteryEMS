"""Energy Management System decision engine."""
from __future__ import annotations
import config

class EMSCore:
    def __init__(self, loads=None):
        self.loads = [dict(x) for x in (loads if loads is not None else config.DEFAULT_LOADS)]
        self.active_source = "NONE"
        self.desired_battery_mode = "idle"
        self.shed_loads = []
        self.blackout_risk = False

    def decide(self, bms_status: dict, grid_status: dict):
        grid_available = bool(grid_status["available"])
        healthy = bms_status["status"] == "OK"
        soc = float(bms_status["soc_percent"])
        source = self._choose_source(grid_available, healthy, soc)
        mode = self._choose_battery_mode(source, healthy, soc)
        shed, risk = self._choose_load_shedding(source, soc)
        self.active_source, self.desired_battery_mode = source, mode
        self.shed_loads, self.blackout_risk = shed, risk
        active = [l["name"] for l in self.loads if l["name"] not in shed]
        battery_power = 0.0
        if mode == "charge": battery_power = max(0.0, bms_status["pack_voltage"] * bms_status["current_a"])
        elif mode == "discharge": battery_power = min(0.0, bms_status["pack_voltage"] * bms_status["current_a"])
        return {
            "active_source": source,
            "battery_mode_commanded": mode,
            "grid_available": grid_available,
            "battery_soc_percent": soc,
            "battery_status": bms_status["status"],
            "battery_faults": list(bms_status.get("faults", [])),
            "active_loads": active,
            "shed_loads": list(shed),
            "blackout_risk": risk,
            "energy_flow": {
                "battery_power_w": round(battery_power, 3),
                "grid_power_w": round(max(0.0, sum(l["watts"] for l in self.loads if l["name"] in active) - max(0.0, battery_power)), 3),
                "load_power_w": round(sum(l["watts"] for l in self.loads if l["name"] in active), 3),
            },
        }

    def _choose_source(self, grid_available, healthy, soc):
        if grid_available: return "GRID"
        if healthy and soc > config.SOC_CRITICAL_PERCENT: return "BATTERY"
        return "NONE"

    def _choose_battery_mode(self, source, healthy, soc):
        if not healthy: return "idle"
        if source == "GRID": return "charge" if soc < config.SOC_STOP_CHARGE_PERCENT else "idle"
        if source == "BATTERY": return "discharge" if soc > config.SOC_CRITICAL_PERCENT else "idle"
        return "idle"

    def _choose_load_shedding(self, source, soc):
        if source == "NONE": return [l["name"] for l in self.loads], True
        if source == "BATTERY" and soc < config.SOC_LOW_SHED_PERCENT:
            return [l["name"] for l in self.loads if not l["critical"]], False
        return [], False
