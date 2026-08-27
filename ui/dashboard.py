from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
)
from PySide6.QtCore import Qt

from ui.widgets.info_card import InfoCard
from ui.widgets.chart_widget import ChartWidget


class DashboardPage(QWidget):

    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("BatteryEMS Dashboard")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-size:28px; font-weight:bold; margin-bottom: 6px;")
        layout.addWidget(title)

        cards = QGridLayout()
        cards.setHorizontalSpacing(14)
        cards.setVerticalSpacing(14)

        self.soc = InfoCard("SOC %", "--")
        self.voltage = InfoCard("Pack Voltage", "--")
        self.current = InfoCard("Current", "--")
        self.temperature = InfoCard("Temperature", "--")

        for widget, row, col in [(self.soc, 0, 0), (self.voltage, 0, 1), (self.current, 1, 0), (self.temperature, 1, 1)]:
            cards.addWidget(widget, row, col)
        layout.addLayout(cards)

        self.status = QLabel()
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("font-size:16px; padding:16px; background:#1F2937; border-radius:12px; border: 1px solid #374151;")
        layout.addWidget(self.status)

        charts = QGridLayout()
        charts.setHorizontalSpacing(14)
        charts.setVerticalSpacing(14)

        self.soc_chart = ChartWidget("SOC (%)")
        self.voltage_chart = ChartWidget("Pack Voltage (V)")
        self.current_chart = ChartWidget("Current (A)")
        self.temperature_chart = ChartWidget("Temperature (°C)")

        charts.addWidget(self.soc_chart, 0, 0)
        charts.addWidget(self.voltage_chart, 0, 1)
        charts.addWidget(self.current_chart, 1, 0)
        charts.addWidget(self.temperature_chart, 1, 1)
        layout.addLayout(charts)

        self.refresh()

    def refresh(self):
        if self.controller is None:
            return

        data = self.controller.get_live_data()

        self.soc.update_value(f"{data['bms']['soc_percent']:.1f} %")
        self.voltage.update_value(f"{data['bms']['pack_voltage']:.2f} V")
        self.current.update_value(f"{data['bms']['current_a']:.2f} A")
        self.temperature.update_value(f"{data['bms']['temperature_c']:.1f} °C")

        history = self.controller.get_history(limit=60) or []
        self.soc_chart.update_chart(values=[float(r.get("soc_percent", 0.0)) for r in history])
        self.voltage_chart.update_chart(values=[float(r.get("pack_voltage", 0.0)) for r in history])
        self.current_chart.update_chart(values=[float(r.get("pack_current", 0.0)) for r in history])
        self.temperature_chart.update_chart(values=[float(r.get("temperature", 0.0)) for r in history])

        faults = ", ".join(data["bms"]["faults"]) if data["bms"]["faults"] else "None"
        balancing = ", ".join(map(str, data["bms"]["balancing_cells"])) if data["bms"]["balancing_cells"] else "None"

        self.status.setText(
            f"Battery Status : {data['bms']['status']}\n\n"
            f"Grid : {'UP' if data['ems']['grid_available'] else 'DOWN'}\n\n"
            f"Mode : {data['ems']['battery_mode_commanded']}\n\n"
            f"Balancing : {balancing}\n\n"
            f"Faults : {faults}"
        )