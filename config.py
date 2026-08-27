"""Central configuration for BatteryEMS.

All safety/operational defaults are centralized here. Real hardware profiles
should override these values only after the connected pack has been verified.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_PATH = str(PROJECT_ROOT / "database" / "bms_data.db")
REPORTS_PATH = str(PROJECT_ROOT / "reports")
LOG_DIRECTORY = str(PROJECT_ROOT / "logs")

# Battery topology / rating
NUM_CELLS = 4
RATED_CAPACITY_AH = 2.5
BATTERY_CAPACITY_AH = RATED_CAPACITY_AH
INITIAL_SOC_PERCENT = 60.0

# Sampling
TICK_INTERVAL_SECONDS = 1.0
UPDATE_INTERVAL = 1.0
MAX_HISTORY_POINTS = 120

# Cell / pack protection limits
CELL_OVERVOLTAGE_THRESHOLD = 4.25
CELL_UNDERVOLTAGE_THRESHOLD = 2.95
PACK_OVERCURRENT_THRESHOLD_A = 5.0
PACK_OVERTEMP_THRESHOLD_C = 55.0
IMBALANCE_TRIGGER_V = 0.05
BALANCE_ACTIVE_ABOVE_V = 3.90

# SOC operating limits
SOC_STOP_CHARGE_PERCENT = 95.0
SOC_LOW_SHED_PERCENT = 20.0
SOC_CRITICAL_PERCENT = 5.0

# SOH framework
SOH_INITIAL_PERCENT = 100.0
SOH_MIN_PERCENT = 70.0
SOH_CYCLE_DEGRADATION_PERCENT = 0.02  # configurable model assumption, not a measured value

# EMS loads
DEFAULT_LOADS = [
    {"name": "Critical Load (e.g. server/comms)", "watts": 400, "critical": True},
    {"name": "Non-Critical Load (e.g. lighting)", "watts": 150, "critical": False},
]

# Simulator
SIMULATION_UPDATE_INTERVAL_MS = int(TICK_INTERVAL_SECONDS * 1000)
START_SIMULATOR_AUTOMATICALLY = True
DATA_LOGGING_ENABLED = True

# Future hardware profile; no protocol is assumed yet.
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
MCU_TIMEOUT = 1.0

THEME = "Dark"
