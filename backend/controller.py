"""Application orchestrator shared by desktop and web interfaces."""
from __future__ import annotations
from datetime import datetime
import threading, time
import config

# --- auto cycle detection tuning ---
# |current| above this counts as active charge/discharge.
AUTO_CYCLE_CURRENT_THRESHOLD_A = 0.15
# consecutive active ticks required before auto-starting a cycle (avoids noise-triggered starts)
AUTO_CYCLE_CONFIRM_TICKS = 3
# consecutive idle ticks required before auto-stopping a cycle (avoids flicker around 0A)
AUTO_CYCLE_IDLE_TICKS_TO_STOP = 10

from backend.bms_core import BMSCore
from backend.ems_core import EMSCore
from backend.grid_sim import SimulatedGrid
from hardware.battery_hardware import SimulatorHardware, RealBMSHardware
from backend.ocv_lookup import voltage_to_soc
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
        self._soc_seeded = False

        # --- cycle testing foundation (logging/labeling only; no hardware control) ---
        self.current_cycle_id = None
        self.test_state = "IDLE"  # IDLE, CHARGE, DISCHARGE
        self._auto_cycle_active = False  # True only if the CURRENT cycle was auto-started
        self._auto_active_ticks = 0
        self._auto_idle_ticks = 0

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

            if (isinstance(self.hardware, RealBMSHardware) and not self._soc_seeded
                    and all(v > 0.5 for v in reading.get("cell_voltages", []))):
                avg_cell_v = sum(reading["cell_voltages"]) / len(reading["cell_voltages"])
                seeded_percent = voltage_to_soc(avg_cell_v)
                self.bms.set_soc_percent(seeded_percent)
                self._soc_seeded = True

            bms = self.bms.update(reading, dt_seconds=dt)
            ems = self.ems.decide(bms, self.grid.read())

            if not self.paused and isinstance(self.hardware, SimulatorHardware):
                self.hardware.set_mode(ems["battery_mode_commanded"])
                self.hardware.tick(config.TICK_INTERVAL_SECONDS)
                bms = self.bms.update(self.hardware.read(), dt_seconds=config.TICK_INTERVAL_SECONDS)
                ems = self.ems.decide(bms, self.grid.read())

            self._auto_detect_cycle(bms.get("current_a", 0.0))

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
                # additive: labels every reading with the active cycle/test state
                "cycle_id": self.current_cycle_id,
                "test_state": self.test_state,
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
        self._soc_seeded = False  # allow a fresh reseed from real voltage on (re)connect
        return self.get_device_status()

    def connect_device(self):
        self.hardware.connect()

        # If this is real hardware and it already has a genuine reading
        # (not the all-zero placeholder for "no data yet"), seed SOC
        # from the actual measured pack voltage instead of a guessed
        # default. Only valid for a resting pack (no active load or
        # charge current) -- voltage sags under load will skew this.
        if isinstance(self.hardware, RealBMSHardware):
            reading = self.hardware.read()
            cells = reading.get("cell_voltages", [])
            if cells and any(v > 0.1 for v in cells):
                avg_cell_v = sum(cells) / len(cells)
                from backend.ocv_lookup import voltage_to_soc
                real_soc = voltage_to_soc(avg_cell_v)
                self.bms.set_soc_percent(real_soc)
                print(f"[CONTROLLER] Seeded SOC from real voltage: "
                      f"{avg_cell_v:.3f}V/cell -> {real_soc:.1f}%")
            else:
                print("[CONTROLLER] No real hardware reading yet -- "
                      "SOC not re-seeded, using previous estimate.")

        return self.get_device_status()

    def disconnect_device(self):
        self.hardware.disconnect()
        return self.get_device_status()

    # --------------------------------------------------------------
    # CYCLE TESTING (additive; pure logging/labeling, no charger/
    # load/relay control of any kind)
    # --------------------------------------------------------------
    def start_cycle(self, test_state="CHARGE"):
        with self._lock:
            test_state = str(test_state or "CHARGE").upper()
            if test_state not in ("CHARGE", "DISCHARGE"):
                test_state = "CHARGE"
            cycle = self.repository.create_cycle(test_state)
            self.current_cycle_id = cycle["id"]
            self.test_state = test_state
            return cycle

    def stop_cycle(self):
        with self._lock:
            stopped_id = self.current_cycle_id
            if stopped_id is not None:
                self.repository.stop_cycle(stopped_id)
            self.current_cycle_id = None
            self.test_state = "IDLE"
            return stopped_id

    def get_cycles(self):
        return self.repository.list_cycles()

    def get_cycle_readings(self, cycle_id):
        return self.repository.get_readings_for_cycle(cycle_id)

    def get_current_cycle_status(self):
        return {"cycle_id": self.current_cycle_id, "test_state": self.test_state}

    def _auto_detect_cycle(self, current_a):
        """
        Automatically starts/stops a cycle record based on real current flow --
        no action needed on the Cycles tab. Only ever acts on a cycle it started
        itself; a cycle started manually via the tab/API is left running until the
        user stops it, exactly as before.
        """
        try:
            current_a = float(current_a)
        except (TypeError, ValueError):
            return

        if current_a >= AUTO_CYCLE_CURRENT_THRESHOLD_A:
            detected_state = "CHARGE"
        elif current_a <= -AUTO_CYCLE_CURRENT_THRESHOLD_A:
            detected_state = "DISCHARGE"
        else:
            detected_state = None

        if detected_state is not None:
            self._auto_idle_ticks = 0
            if self.current_cycle_id is None:
                self._auto_active_ticks += 1
                if self._auto_active_ticks >= AUTO_CYCLE_CONFIRM_TICKS:
                    self.start_cycle(detected_state)
                    self._auto_cycle_active = True
                    self._auto_active_ticks = 0
            elif self._auto_cycle_active and self.test_state != detected_state:
                # direction flipped (charge <-> discharge) -- close old cycle, open a new one
                self.stop_cycle()
                self.start_cycle(detected_state)
                self._auto_cycle_active = True
                self._auto_active_ticks = 0
        else:
            self._auto_active_ticks = 0
            if self.current_cycle_id is not None and self._auto_cycle_active:
                self._auto_idle_ticks += 1
                if self._auto_idle_ticks >= AUTO_CYCLE_IDLE_TICKS_TO_STOP:
                    self.stop_cycle()
                    self._auto_cycle_active = False
                    self._auto_idle_ticks = 0
            else:
                self._auto_idle_ticks = 0
