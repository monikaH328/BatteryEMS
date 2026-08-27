from backend.bms_core import BMSCore
from backend.ems_core import EMSCore
from backend.soc_estimator import CoulombCounter
def reading(cells=(3.7,3.7,3.7,3.7),current=0,temp=25): return {"cell_voltages":list(cells),"current_a":current,"temperature_c":temp}
def test_soc_charge_and_discharge():
    s=CoulombCounter(2.5,50); s.update(2.5,3600); assert s.soc_percent==100; s.update(-2.5,3600); assert s.soc_percent==0
def test_soc_never_exceeds_bounds():
    s=CoulombCounter(2.5,50); s.update(100,3600); assert s.soc_percent==100; s.update(-100,3600); assert s.soc_percent==0
def test_protection_limits():
    b=BMSCore(); faults=b.update(reading((4.3,3.7,3.7,3.7),8,60),0)["faults"]
    assert any("OVERVOLTAGE" in f for f in faults) and any("OVERCURRENT" in f for f in faults) and any("OVERTEMPERATURE" in f for f in faults)
def test_imbalance_detection():
    b=BMSCore(); s=b.update(reading((3.95,3.85,4.05,3.85)),0); assert s["imbalance_v"]==0.2 and 2 in s["balancing_cells"]
def test_grid_and_charge_decision():
    e=EMSCore(); s=e.decide({"status":"OK","soc_percent":75,"pack_voltage":14.8,"current_a":0,"faults":[]},{"available":True}); assert s["active_source"]=="GRID" and s["battery_mode_commanded"]=="charge"
def test_grid_down_discharge():
    e=EMSCore(); s=e.decide({"status":"OK","soc_percent":60,"pack_voltage":14.8,"current_a":-1.5,"faults":[]},{"available":False}); assert s["active_source"]=="BATTERY" and s["battery_mode_commanded"]=="discharge"
def test_fault_state():
    b=BMSCore(); s=b.update(reading((4.3,3.7,3.7,3.7),7,58),1); assert s["status"]=="FAULT" and len(s["faults"])>=3
