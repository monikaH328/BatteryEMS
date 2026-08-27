"""SOH framework.

SOH is reported from estimated usable capacity versus rated capacity. The
simulator starts at 100%; real SOH should later be calibrated from measured
capacity tests and the connected BMS data.
"""
from __future__ import annotations

class SOHEstimator:
    def __init__(self, rated_capacity_ah: float, initial_soh_percent: float = 100.0):
        self.rated_capacity_ah = float(rated_capacity_ah)
        self.initial_soh_percent = float(initial_soh_percent)
        self.available_capacity_ah = self.rated_capacity_ah * self.initial_soh_percent / 100.0

    def update(self, usable_capacity_ah: float | None = None) -> float:
        if usable_capacity_ah is not None:
            self.available_capacity_ah = max(0.0, min(self.rated_capacity_ah, float(usable_capacity_ah)))
        return self.soh_percent

    @property
    def soh_percent(self) -> float:
        return round(100.0 * self.available_capacity_ah / self.rated_capacity_ah, 2)
