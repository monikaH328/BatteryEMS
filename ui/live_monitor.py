from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QGroupBox,
)
import config
from PySide6.QtCore import Qt


class LiveMonitorPage(QWidget):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.setStyleSheet("""
            QWidget { background: #111827; color: white; }
            QLabel { color: white; }
            QGroupBox { border: 1px solid #374151; border-radius: 12px; margin-top: 14px; padding-top: 12px; color: white; background: #111827; }
            QPushButton { background: #1F2937; border: 1px solid #374151; border-radius: 8px; color: white; padding: 8px 12px; }
            QPushButton:hover { background: #0F766E; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Live Monitor")
        title.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 8px;")
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        self.summary = QGridLayout()
        self.summary.setHorizontalSpacing(16)
        self.summary.setVerticalSpacing(12)

        self.soc_label = QLabel("--")
        self.voltage_label = QLabel("--")
        self.current_label = QLabel("--")
        self.temp_label = QLabel("--")
        self.mode_label = QLabel("--")
        self.status_label = QLabel("--")

        for label, value, row, col in [
            ("SOC", self.soc_label, 0, 0),
            ("Pack Voltage", self.voltage_label, 0, 1),
            ("Current", self.current_label, 1, 0),
            ("Temperature", self.temp_label, 1, 1),
            ("Battery Mode", self.mode_label, 2, 0),
            ("Battery Status", self.status_label, 2, 1),
        ]:
            name = QLabel(label)
            name.setStyleSheet("color: #9CA3AF; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;")
            value.setStyleSheet("font-size: 24px; font-weight: bold; color: #14B8A6;")
            value.setAlignment(Qt.AlignLeft)
            self.summary.addWidget(name, row * 2, col)
            self.summary.addWidget(value, row * 2 + 1, col)
        layout.addLayout(self.summary)

        self.cells_box = QGroupBox("Cell Monitoring")
        cells_layout = QVBoxLayout(self.cells_box)

        self.cell_values = []
        self.cell_grid = QGridLayout()
        for idx in range(config.NUM_CELLS):
            cell_name = QLabel(f"Cell {idx + 1}")
            cell_name.setStyleSheet("color: #9CA3AF; font-weight: bold;")
            cell_value = QLabel("-- V")
            cell_value.setStyleSheet("font-size: 18px; font-weight: bold;")
            self.cell_values.append(cell_value)
            self.cell_grid.addWidget(cell_name, idx, 0)
            self.cell_grid.addWidget(cell_value, idx, 1)
        cells_layout.addLayout(self.cell_grid)

        spread_box = QHBoxLayout()
        self.max_cell = QLabel("Max: -- V")
        self.min_cell = QLabel("Min: -- V")
        self.spread_label = QLabel("Spread: -- V")
        for w in (self.max_cell, self.min_cell, self.spread_label):
            w.setStyleSheet("background: #1F2937; border: 1px solid #374151; border-radius: 8px; padding: 8px; color: white;")
            w.setAlignment(Qt.AlignCenter)
            spread_box.addWidget(w)
        cells_layout.addLayout(spread_box)

        self.balancing_label = QLabel("Balancing: None")
        self.balancing_label.setStyleSheet("background: #0F172A; border: 1px solid #374151; border-radius: 8px; padding: 10px;")
        cells_layout.addWidget(self.balancing_label)
        layout.addWidget(self.cells_box)

        controls = QGroupBox("Protection Test")
        controls_layout = QGridLayout(controls)
        actions = [
            ("Inject OV", "overvoltage"),
            ("Inject UV", "undervoltage"),
            ("Inject OC", "overcurrent"),
            ("Inject OT", "overtemp"),
            ("Inject Imbalance", "imbalance"),
            ("Clear Faults", "clear"),
        ]
        for index, (label, key) in enumerate(actions):
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked=False, k=key: self.handle_action(k))
            controls_layout.addWidget(btn, index // 2, index % 2)
        layout.addWidget(controls)

        self.refresh()

    def handle_action(self, action):
        if self.controller is None:
            return
        if action == "clear":
            self.controller.clear_faults()
        else:
            self.controller.inject_fault(action)
        self.refresh()

    def refresh(self):
        if self.controller is None:
            return
        data = self.controller.get_live_data()
        cells = data.get("bms", {}).get("cell_voltages", [3.7, 3.7, 3.7, 3.7])
        for idx, value in enumerate(cells[:4]):
            self.cell_values[idx].setText(f"{value:.3f} V")
        if len(cells) >= 4:
            self.max_cell.setText(f"Max: {max(cells):.3f} V")
            self.min_cell.setText(f"Min: {min(cells):.3f} V")
            self.spread_label.setText(f"Spread: {max(cells) - min(cells):.3f} V")

        self.soc_label.setText(f"{data.get('bms', {}).get('soc_percent', 0):.1f}%")
        self.voltage_label.setText(f"{data.get('bms', {}).get('pack_voltage', 0):.2f} V")
        self.current_label.setText(f"{data.get('bms', {}).get('current_a', 0):.2f} A")
        self.temp_label.setText(f"{data.get('bms', {}).get('temperature_c', 0):.1f} °C")
        self.mode_label.setText(str(data.get("ems", {}).get("battery_mode_commanded", "idle")).title())
        self.status_label.setText(str(data.get("bms", {}).get("status", "OK")))
        self.status_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; border-radius: 12px; padding: 8px 10px; "
            + self._style_for_status(data.get("bms", {}).get("status", "OK"))
        )

        balancing = data.get("bms", {}).get("balancing_cells") or []
        if balancing:
            self.balancing_label.setText(f"Balancing cells: {', '.join(str(v + 1) for v in balancing)}")
        else:
            self.balancing_label.setText("Balancing: None")

    def _style_for_status(self, status):
        status = str(status).upper()
        if status == "OK":
            return "background: #022C22; color: #6EE7B7; border: 1px solid #065F46;"
        if status == "FAULT":
            return "background: #450A0A; color: #FCA5A5; border: 1px solid #991B1B;"
        if status == "WARNING":
            return "background: #451A03; color: #FCD34D; border: 1px solid #B45309;"
        return "background: #1F2937; color: #D1D5DB; border: 1px solid #374151;"
