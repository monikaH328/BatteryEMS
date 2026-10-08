"""
battery_sim.py
Simulates a 4-cell battery pack: voltages, current, temperature.
This is a FAKE battery -- no real hardware involved. It behaves
"reasonably realistically" so BMS logic can be developed and tested
before any real cells are connected.

You can inject faults on demand (see inject_fault) to test that your
BMS protection logic actually catches them.
"""
import config


import random

NUM_CELLS = config.NUM_CELLS

# Reasonable Li-ion single-cell voltage bounds (volts)
CELL_NOMINAL_V = 3.7
CELL_MAX_V = 4.2
CELL_MIN_V = 3.0

# Ambient starting temperature (Celsius)
AMBIENT_TEMP_C = 25.0


class SimulatedBattery:
    def __init__(self):
        # Start each cell slightly different, like a real pack would be
        self.cell_voltages = [
            round(CELL_NOMINAL_V + random.uniform(-0.03, 0.03), 3)
            for _ in range(NUM_CELLS)
        ]
        self.current_a = 0.0          # positive = charging, negative = discharging
        self.temperature_c = AMBIENT_TEMP_C
        self.mode = "idle"            # "idle" | "charge" | "discharge"

        # Coulomb counting needs a starting capacity assumption
        self.rated_capacity_ah = 2.5          # per cell, typical 18650-ish
        self.remaining_capacity_ah = self.rated_capacity_ah * 0.6  # start at 60%

        # Internal fault flags (forced by inject_fault, cleared by clear_faults)
        self._forced_fault = None

    # ------------------------------------------------------------------
    # Mode control
    # ------------------------------------------------------------------
    def set_mode(self, mode: str):
        if mode not in ("idle", "charge", "discharge"):
            print(f"[SIM] Unknown mode '{mode}', ignoring.")
            return
        self.mode = mode
        print(f"[SIM] Mode set to: {mode}")

    # ------------------------------------------------------------------
    # Fault injection (for testing your BMS protection logic)
    # ------------------------------------------------------------------
    def inject_fault(self, fault_type: str):
        """
        fault_type: 'overvoltage' | 'undervoltage' | 'overcurrent' | 'overtemp' | 'imbalance'
        Forces the simulated readings toward an unsafe condition so you
        can confirm your BMS catches it.
        """
        self._forced_fault = fault_type
        print(f"[SIM] Fault injected: {fault_type}")

    def clear_faults(self):
        self._forced_fault = None
        print("[SIM] Forced faults cleared. Returning to normal simulation.")

    # ------------------------------------------------------------------
    # Core tick -- advances the simulated battery by one time step
    # ------------------------------------------------------------------
    def tick(self, dt_seconds: float = 1.0):
        self._apply_mode_physics(dt_seconds)
        self._apply_forced_fault()
        self._update_capacity(dt_seconds)

    def _apply_mode_physics(self, dt_seconds):
        if self.mode == "charge":
            self.current_a = 1.0  # amps, positive = into the battery
            for i in range(NUM_CELLS):
                drift = random.uniform(0.0008, 0.0015)  # slight cell-to-cell variance
                self.cell_voltages[i] = min(
                    CELL_MAX_V + 0.05,  # allow slight overshoot so OV logic has something to catch
                    self.cell_voltages[i] + drift,
                )
            self.temperature_c += 0.05 * dt_seconds

        elif self.mode == "discharge":
            self.current_a = -1.5
            for i in range(NUM_CELLS):
                drift = random.uniform(0.0008, 0.002)
                self.cell_voltages[i] = max(
                    CELL_MIN_V - 0.05,
                    self.cell_voltages[i] - drift,
                )
            self.temperature_c += 0.08 * dt_seconds

        else:  # idle
            self.current_a = 0.0
            # cool toward ambient
            if self.temperature_c > AMBIENT_TEMP_C:
                self.temperature_c -= 0.1 * dt_seconds
                self.temperature_c = max(AMBIENT_TEMP_C, self.temperature_c)

    def _apply_forced_fault(self):
        if self._forced_fault is None:
            return

        if self._forced_fault == "overvoltage":
            self.cell_voltages[0] = CELL_MAX_V + 0.15
        elif self._forced_fault == "undervoltage":
            self.cell_voltages[1] = CELL_MIN_V - 0.15
        elif self._forced_fault == "overcurrent":
            self.current_a = -8.0 if self.mode == "discharge" else 6.0
        elif self._forced_fault == "overtemp":
            self.temperature_c = 65.0
        elif self._forced_fault == "imbalance":
            self.cell_voltages[2] = self.cell_voltages[2] + 0.2

    def _update_capacity(self, dt_seconds):
        # Coulomb counting on the sim side too, just to track "ground truth"
        # (your BMS will do its OWN estimate from current -- this is separate)
        delta_ah = (self.current_a * dt_seconds) / 3600.0
        self.remaining_capacity_ah += delta_ah
        self.remaining_capacity_ah = max(
            0.0, min(self.rated_capacity_ah, self.remaining_capacity_ah)
        )

    # ------------------------------------------------------------------
    # Read interface -- this is what a real BMS AFE chip would give you
    # ------------------------------------------------------------------
    def read(self):
        return {
            "cell_voltages": list(self.cell_voltages),
            "current_a": round(self.current_a, 3),
            "temperature_c": round(self.temperature_c, 2),
            "mode": self.mode,
        }