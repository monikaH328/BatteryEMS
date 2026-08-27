"""
grid_sim.py
A deliberately simple simulated grid connection. Real grid monitoring
would involve voltage/frequency sensing, but for this prototype we only
need "is the grid available or not" -- that's enough to drive real
EMS source-switching decisions.
"""


class SimulatedGrid:
    def __init__(self):
        self.available = True

    def set_available(self, available: bool):
        self.available = available
        state = "UP" if available else "DOWN"
        print(f"[GRID] Grid is now {state}")

    def read(self):
        return {"available": self.available}