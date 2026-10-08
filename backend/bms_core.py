"""Hardware-independent BMS calculations and protection logic."""
from __future__ import annotations
from datetime import datetime
import config
from backend.soc_estimator import CoulombCounter
from backend.soh_estimator import SOHEstimator
from backend.ocv_lookup import voltage_to_soc

# --- OCV correction tuning ---
# |current| below this counts as "at rest" for OCV purposes.
REST_CURRENT_THRESHOLD_A = 0.10
# consecutive rest ticks required before trusting OCV (lets voltage settle after current stops)
REST_CONFIRM_TICKS = 10
# fraction of the gap to OCV-implied SOC closed per tick once at rest (small = gentle correction)
SOC_CORRECTION_GAIN = 0.04

class BMSCore:
    def __init__(self, rated_capacity_ah: float = config.RATED_CAPACITY_AH,
                 initial_soc_percent: float = config.INITIAL_SOC_PERCENT):
        self.rated_capacity_ah = rated_capacity_ah
        self.soc_estimator = CoulombCounter(rated_capacity_ah, initial_soc_percent)
        self.soh_estimator = SOHEstimator(rated_capacity_ah, config.SOH_INITIAL_PERCENT)
        self.last_status = "OK"
        self.active_faults: list[str] = []
        self.balancing_cells: list[int] = []
        self._rest_ticks = 0

    def set_soc_percent(self, percent: float):
        """
        Directly reseeds the SOC estimate -- used when connecting real
        hardware, to start Coulomb counting from an actual measured
        voltage-derived SOC instead of a guessed default.
        """
        percent = max(0.0, min(100.0, percent))
        self.soc_estimator.estimated_capacity_ah = self.soc_estimator.capacity_ah * (percent / 100.0)

    def seed_cycles(self, saved_cycles: float):
        """
        Restores the coulomb counter's lifetime throughput from the last
        equivalent_full_cycles value saved to the DB, so cycle count survives
        an app restart instead of resetting to 0 each time.
        """
        saved_cycles = max(0.0, float(saved_cycles))
        self.soc_estimator.amp_hours_throughput = saved_cycles * 2.0 * self.rated_capacity_ah

    def update(self, reading: dict, dt_seconds: float = 1.0):
        cells = [float(v) for v in reading["cell_voltages"]]
        current = float(reading["current_a"])
        temp = float(reading["temperature_c"])
        faults = self._check_protections(cells, current, temp)
        self.soc_estimator.update(current, dt_seconds)

        # OCV-based SOC correction: pulls the coulomb-counter estimate toward
        # the voltage-derived SOC once the pack has rested long enough for
        # voltage to settle, so SOC stops drifting indefinitely.
        if cells and all(v > 0.5 for v in cells) and abs(current) < REST_CURRENT_THRESHOLD_A:
            self._rest_ticks += 1
        else:
            self._rest_ticks = 0

        if self._rest_ticks >= REST_CONFIRM_TICKS:
            avg_cell_v = sum(cells) / len(cells)
            ocv_soc_percent = voltage_to_soc(avg_cell_v)
            ocv_capacity_ah = self.rated_capacity_ah * ocv_soc_percent / 100.0
            current_ah = self.soc_estimator.estimated_capacity_ah
            self.soc_estimator.estimated_capacity_ah = current_ah + SOC_CORRECTION_GAIN * (ocv_capacity_ah - current_ah)

        self.soh_estimator.update()
        self.balancing_cells = self._check_balancing(cells)
        self.active_faults = faults
        self.last_status = "FAULT" if faults else "OK"

        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "status": self.last_status,
            "faults": list(faults),
            "soc_percent": self.soc_estimator.soc_percent,
            "soh_percent": self.soh_estimator.soh_percent,
            "cell_voltages": cells,
            "pack_voltage": round(sum(cells), 4),
            "current_a": round(current, 4),
            "temperature_c": round(temp, 2),
            "balancing_cells": list(self.balancing_cells),
            "imbalance_v": round(max(cells) - min(cells), 4),
            "estimated_capacity_ah": round(self.soc_estimator.estimated_capacity_ah, 5),
            "equivalent_full_cycles": round(self.soc_estimator.equivalent_full_cycles, 5),
        }

    def _check_protections(self, cells, current_a, temperature_c):
        faults = []
        for idx, v in enumerate(cells):
            if v <= 0.0:
                continue  # no real reading yet for this cell -- not an actual fault, skip check
            if v >= config.CELL_OVERVOLTAGE_THRESHOLD:
                faults.append(f"OVERVOLTAGE: cell {idx} at {v:.3f}V (limit {config.CELL_OVERVOLTAGE_THRESHOLD}V)")
            if v <= config.CELL_UNDERVOLTAGE_THRESHOLD:
                faults.append(f"UNDERVOLTAGE: cell {idx} at {v:.3f}V (limit {config.CELL_UNDERVOLTAGE_THRESHOLD}V)")
        if abs(current_a) >= config.PACK_OVERCURRENT_THRESHOLD_A:
            faults.append(f"OVERCURRENT: {current_a:.2f}A (limit {config.PACK_OVERCURRENT_THRESHOLD_A}A)")
        if temperature_c >= config.PACK_OVERTEMP_THRESHOLD_C:
            faults.append(f"OVERTEMPERATURE: {temperature_c:.1f}C (limit {config.PACK_OVERTEMP_THRESHOLD_C}C)")
        return faults

    def _check_balancing(self, cells):
        max_v, min_v = max(cells), min(cells)
        if max_v < config.BALANCE_ACTIVE_ABOVE_V or max_v - min_v < config.IMBALANCE_TRIGGER_V:
            return []
        return [i for i, v in enumerate(cells) if v - min_v >= config.IMBALANCE_TRIGGER_V]

    def get_soc_percent(self):
        return self.soc_estimator.soc_percent
