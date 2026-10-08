"""
Thread-safe in-memory store for the latest battery reading pushed by
real hardware (e.g. an ESP32) via POST /api/ingest.

This exists because a cloud-hosted app cannot reach out and poll a
device sitting on someone's home network -- the device must push data
TO the server instead. This module just holds "whatever was pushed
most recently" and how long ago that was.
"""
import threading
import time

_lock = threading.Lock()
_latest = None
_last_received_monotonic = 0.0


# TEMP FIX: firmware's ACS712 sign is inverted (discharge reads positive,
# charge reads negative). Flip here until the .ino is reflashed with
# CURRENT_SIGN = -1.0. Remove this multiplier once that reflash is done,
# to avoid double-inverting.
CURRENT_SIGN_CORRECTION = -1.0

def store_reading(cell_voltages, current_a, temperature_c):
    global _latest, _last_received_monotonic
    with _lock:
        _latest = {
            "cell_voltages": [float(v) for v in cell_voltages],
            "current_a": float(current_a) * CURRENT_SIGN_CORRECTION,
            "temperature_c": float(temperature_c),
        }
        _last_received_monotonic = time.monotonic()


def get_latest():
    with _lock:
        return dict(_latest) if _latest is not None else None


def seconds_since_last_reading():
    with _lock:
        if _last_received_monotonic == 0.0:
            return None
        return time.monotonic() - _last_received_monotonic
