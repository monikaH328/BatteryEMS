"""Hardware abstraction layer for BatteryEMS."""
from __future__ import annotations
from abc import ABC, abstractmethod
from backend.battery_sim import SimulatedBattery

class BatteryHardwareInterface(ABC):
    @abstractmethod
    def read(self) -> dict: ...
    @abstractmethod
    def set_mode(self, mode: str) -> None: ...
    @abstractmethod
    def tick(self, dt_seconds: float = 1.0) -> None: ...
    @abstractmethod
    def inject_fault(self, fault_type: str) -> None: ...
    @abstractmethod
    def clear_faults(self) -> None: ...
    @abstractmethod
    def connect(self) -> None: ...
    @abstractmethod
    def disconnect(self) -> None: ...
    @property
    @abstractmethod
    def connected(self) -> bool: ...

class SimulatorHardware(BatteryHardwareInterface):
    def __init__(self):
        self.battery = SimulatedBattery()
        self._connected = True
    def read(self): return self.battery.read()
    def set_mode(self, mode): self.battery.set_mode(mode)
    def tick(self, dt_seconds=1.0): self.battery.tick(dt_seconds)
    def inject_fault(self, fault_type): self.battery.inject_fault(fault_type)
    def clear_faults(self): self.battery.clear_faults()
    def connect(self): self._connected = True
    def disconnect(self): self._connected = False
    @property
    def connected(self): return self._connected

class RealBMSHardware(BatteryHardwareInterface):
    """Safe placeholder. No protocol is invented or opened."""
    def __init__(self, transport=None):
        self.transport = transport
        self._connected = False
    def read(self):
        raise NotImplementedError("RealBMSHardware needs the actual BMS/ESP32 protocol.")
    def set_mode(self, mode): raise NotImplementedError
    def tick(self, dt_seconds=1.0): pass
    def inject_fault(self, fault_type): raise NotImplementedError
    def clear_faults(self): raise NotImplementedError
    def connect(self): raise NotImplementedError("Add the verified hardware transport before connecting.")
    def disconnect(self): self._connected = False
    @property
    def connected(self): return self._connected
