from backend.battery_sim import SimulatedBattery
from backend.bms_core import BMSCore
from backend.grid_sim import SimulatedGrid
from backend.ems_core import EMSCore


class Simulation:

    def __init__(self):

        self.battery = SimulatedBattery()
        self.bms = BMSCore()
        self.grid = SimulatedGrid()
        self.ems = EMSCore()

    def step(self):

        # Initial BMS update
        bms = self.bms.update(
            self.battery.read(),
            dt_seconds=0
        )

        # EMS decides charging/discharging
        self.ems.decide(
            bms,
            self.grid.read()
        )

        # Apply battery mode
        self.battery.set_mode(
            self.ems.desired_battery_mode
        )

        # Advance battery simulation
        self.battery.tick()

        # Read updated battery values
        bms = self.bms.update(
            self.battery.read()
        )

        ems = self.ems.decide(
            bms,
            self.grid.read()
        )

        return {
            "bms": bms,
            "ems": ems
        }