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
    """
    Reads real hardware data that the ESP32 PUSHES to this server via
    POST /api/ingest (see app.py and hardware/ingest_store.py).

    This does NOT reach out to the ESP32's IP address -- that only
    works when this app runs on the same local network as the ESP32.
    For a publicly deployed app (e.g. on Render), the ESP32 must push
    its readings to us instead, since the cloud cannot reach into a
    home network. See firmware/esp32_bms_firmware_push/ for the
    matching firmware.
    """
    def __init__(self, transport=None):
        self.transport = transport
        self._connected = False

    def read(self):
        from hardware.ingest_store import get_latest
        latest = get_latest()
        if latest is None:
            return {"cell_voltages": [0.0, 0.0, 0.0, 0.0], "current_a": 0.0, "temperature_c": 0.0}
        return dict(latest)

    def set_mode(self, mode):
        # No physical control path from a cloud server back to the
        # ESP32 in push mode -- this is monitoring-only, matching the
        # real circuit (no ESP32-controlled MOSFETs). Logged only.
        pass

    def tick(self, dt_seconds=1.0):
        pass  # data arrives asynchronously whenever the ESP32 pushes

    def inject_fault(self, fault_type):
        pass  # not applicable to real hardware readings

    def clear_faults(self):
        pass

    def connect(self):
        self._connected = True

    def disconnect(self):
        self._connected = False

    @property
    def connected(self):
        import config
        from hardware.ingest_store import get_latest, seconds_since_last_reading
        age = seconds_since_last_reading()
        return get_latest() is not None and age is not None and age <= config.INGEST_STALE_SECONDS
