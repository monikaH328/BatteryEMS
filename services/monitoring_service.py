"""System monitoring service."""
from backend.controller import BatteryController
class MonitoringService:
    def __init__(self, controller=None): self.controller=controller or BatteryController()
    def tick(self): return self.controller.get_live_data()
    def current_state(self): return self.controller.last_snapshot or self.tick()
