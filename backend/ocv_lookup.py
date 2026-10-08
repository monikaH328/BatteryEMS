"""
Converts a real, measured LiFePO4 cell voltage into an estimated SOC%,
used to seed/correct the Coulomb counter when real hardware connects.

NOTE: LiFePO4's discharge curve is very flat through the middle (most
capacity sits between ~3.0V-3.3V per cell), so this table is deliberately
denser in that range. This reads voltage AT REST (no significant charge/
discharge current) -- under load, voltage sags below true SOC; while
charging, it reads higher than true SOC.

Tune this against your actual pack once you've done a full charge/rest
cycle: note the resting voltage at 0%, 25%, 50%, 75%, 100% and replace
these points with your real numbers for better accuracy.
"""

LIFEPO4_OCV_CURVE = [
    (2.00, 0),
    (2.50, 2),
    (2.80, 5),
    (2.90, 10),
    (3.00, 20),
    (3.10, 40),
    (3.20, 60),
    (3.25, 70),
    (3.30, 80),
    (3.35, 90),
    (3.40, 95),
    (3.45, 98),
    (3.65, 100),
]


def voltage_to_soc(cell_voltage: float) -> float:
    """Linear interpolation across the LiFePO4 OCV curve. Clamps to 0-100."""
    if cell_voltage <= LIFEPO4_OCV_CURVE[0][0]:
        return LIFEPO4_OCV_CURVE[0][1]
    if cell_voltage >= LIFEPO4_OCV_CURVE[-1][0]:
        return LIFEPO4_OCV_CURVE[-1][1]

    for (v_low, soc_low), (v_high, soc_high) in zip(LIFEPO4_OCV_CURVE, LIFEPO4_OCV_CURVE[1:]):
        if v_low <= cell_voltage <= v_high:
            fraction = (cell_voltage - v_low) / (v_high - v_low)
            return soc_low + fraction * (soc_high - soc_low)

    return 0.0
