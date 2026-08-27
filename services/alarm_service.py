"""Alarm service with edge detection for new BMS faults."""
class AlarmService:
    def __init__(self): self.last_faults=set()
    def evaluate(self,bms_state):
        faults=set(bms_state.get("faults",[])); new=sorted(faults-self.last_faults); self.last_faults=faults
        return {"active":sorted(faults),"new":new,"has_alarm":bool(faults)}
