"""Application orchestrator shared by desktop and web interfaces."""
from __future__ import annotations
from datetime import datetime
import threading, time
import config
from backend.bms_core import BMSCore
from backend.ems_core import EMSCore
from backend.grid_sim import SimulatedGrid
from hardware.battery_hardware import SimulatorHardware, RealBMSHardware
from database.repository import BatteryReadingRepository

class BatteryController:
    def __init__(self, hardware=None, repository=None):
        self.hardware = hardware or SimulatorHardware()
        self.grid = SimulatedGrid()
        self.bms = BMSCore()
        self.ems = EMSCore()
        self.repository = repository or BatteryReadingRepository()
        self.paused = False
        self.last_snapshot = None
        self._lock = threading.RLock()
        self._last_tick = time.monotonic()

    @property
    def active_device_name(self):
        return "Simulator" if isinstance(self.hardware, SimulatorHardware) else "Real BMS"

    def _step_simulation(self):
        with self._lock:
            now = time.monotonic()
            dt = min(5.0, max(0.0, now - self._last_tick))
            self._last_tick = now
            if self.last_snapshot is None:
                dt = 0.0

            reading = self.hardware.read()
            bms = self.bms.update(reading, dt_seconds=dt)
            ems = self.ems.decide(bms, self.grid.read())

            if not self.paused and isinstance(self.hardware, SimulatorHardware):
                self.hardware.set_mode(ems["battery_mode_commanded"])
                self.hardware.tick(config.TICK_INTERVAL_SECONDS)
                bms = self.bms.update(self.hardware.read(), dt_seconds=config.TICK_INTERVAL_SECONDS)
                ems = self.ems.decide(bms, self.grid.read())

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            snapshot = {
                "timestamp": timestamp,
                "bms": bms,
                "ems": ems,
                "hardware": {
                    "device": self.active_device_name,
                    "connected": self.hardware.connected,
                    "simulator": isinstance(self.hardware, SimulatorHardware),
                },
                "simulation_running": not self.paused,
            }
            self.last_snapshot = snapshot

            if config.DATA_LOGGING_ENABLED:
                try:
                    self.repository.save_snapshot(snapshot)
                except Exception:
                    pass
            return snapshot

    def update(self): return self._step_simulation()
    def get_live_data(self): return self._step_simulation()

    def get_history(self, limit=120): return self.repository.get_recent(limit)
    def get_statistics(self): return self.repository.get_statistics()
    def get_fault_records(self, limit=100): return self.repository.get_fault_records(limit)

    def set_grid(self, available):
        self.grid.set_available(bool(available))
        return self.get_live_data()
    def grid_up(self): return self.set_grid(True)
    def grid_down(self): return self.set_grid(False)

    def inject_fault(self, fault):
        self.hardware.inject_fault(str(fault).lower())
        return self.get_live_data()
    def clear_faults(self):
        self.hardware.clear_faults()
        return self.get_live_data()

    def pause(self): self.paused = True; return True
    def resume(self): self.paused = False; self._last_tick = time.monotonic(); return True

    def reset(self):
        with self._lock:
            self.hardware = SimulatorHardware()
            self.grid = SimulatedGrid()
            self.bms = BMSCore()
            self.ems = EMSCore()
            self.paused = False
            self.last_snapshot = None
            self._last_tick = time.monotonic()
        return self.get_live_data()

    def get_device_status(self):
        return {"device": self.active_device_name, "connection": "Connected" if self.hardware.connected else "Disconnected",
                "type": "simulator" if isinstance(self.hardware, SimulatorHardware) else "real_bms"}

    def set_active_device(self, device_name):
        if str(device_name).lower() == "esp32":
            self.hardware.disconnect()
            self.hardware = RealBMSHardware()
        else:
            self.hardware = SimulatorHardware()
        self.last_snapshot = None
        self._last_tick = time.monotonic()
        return self.get_device_status()

    def connect_device(self):
        self.hardware.connect()
        return self.get_device_status()

    def disconnect_device(self):
        self.hardware.disconnect()
        return self.get_device_status()
