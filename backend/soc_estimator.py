"""Battery SOC estimation using coulomb counting.

The estimator integrates signed current over elapsed time. Positive current
means charge into the battery; negative current means discharge. This is the
production-safe baseline for the simulator and a hardware-independent core.

OCV/model-based correction is intentionally not enabled because a valid
cell-chemistry OCV curve has not been supplied.
"""
from __future__ import annotations

class CoulombCounter:
    def __init__(self, capacity_ah: float, initial_soc_percent: float = 60.0):
        if capacity_ah <= 0:
            raise ValueError("capacity_ah must be positive")
        self.capacity_ah = float(capacity_ah)
        self.estimated_capacity_ah = self.capacity_ah * float(initial_soc_percent) / 100.0
        self.amp_hours_throughput = 0.0

    def update(self, current_a: float, dt_seconds: float) -> float:
        dt_seconds = max(0.0, float(dt_seconds))
        delta_ah = float(current_a) * dt_seconds / 3600.0
        self.estimated_capacity_ah = min(
            self.capacity_ah,
            max(0.0, self.estimated_capacity_ah + delta_ah),
        )
        self.amp_hours_throughput += abs(delta_ah)
        return self.soc_percent

    @property
    def soc_percent(self) -> float:
        return round(100.0 * self.estimated_capacity_ah / self.capacity_ah, 2)

    @property
    def equivalent_full_cycles(self) -> float:
        return self.amp_hours_throughput / (2.0 * self.capacity_ah)
