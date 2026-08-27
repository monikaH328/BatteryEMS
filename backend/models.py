"""Typed, serializable state models used across BMS, EMS, services and APIs."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass
class BMSState:
    timestamp: str
    soc_percent: float
    soh_percent: float
    cell_voltages: list[float]
    pack_voltage: float
    current_a: float
    temperature_c: float
    status: str
    faults: list[str] = field(default_factory=list)
    balancing_cells: list[int] = field(default_factory=list)
    imbalance_v: float = 0.0
    estimated_capacity_ah: float = 0.0
    equivalent_full_cycles: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class EMSState:
    active_source: str
    battery_mode_commanded: str
    grid_available: bool
    battery_status: str
    battery_soc_percent: float
    active_loads: list[str]
    shed_loads: list[str]
    blackout_risk: bool
    energy_flow: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class SystemState:
    timestamp: str
    bms: BMSState
    ems: EMSState
    hardware: dict[str, Any]
    simulation_running: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
