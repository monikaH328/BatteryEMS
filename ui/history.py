from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QDateEdit,
    QFormLayout,
    QMessageBox,
)

from ui.widgets.chart_widget import ChartWidget


class HistoryPage(QWidget):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.setStyleSheet("""
            QWidget { background: #111827; color: white; }
            QLabel { color: white; }
            QTableWidget { background: #111827; color: white; alternate-background-color: #1F2937; selection-background-color: #0F766E; }
            QPushButton { background: #1F2937; border: 1px solid #374151; border-radius: 8px; color: white; padding: 8px 12px; }
            QPushButton:hover { background: #0F766E; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("History")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)

        filter_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        filter_layout.addWidget(self.refresh_button)
        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Timestamp",
            "SOC",
            "Pack Voltage",
            "Current",
            "Temperature",
            "Battery Status",
            "Grid Status",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        layout.addWidget(self.table)

        chart_layout = QVBoxLayout()
        self.soc_chart = ChartWidget("Historical SOC")
        self.voltage_chart = ChartWidget("Historical Voltage")
        self.current_chart = ChartWidget("Historical Current")
        self.temperature_chart = ChartWidget("Historical Temperature")
        for chart in (self.soc_chart, self.voltage_chart, self.current_chart, self.temperature_chart):
            chart.setMinimumHeight(140)
            chart_layout.addWidget(chart)
        layout.addLayout(chart_layout)

        self.refresh()

    def refresh(self):
        if self.controller is None:
            return
        try:
            data = self.controller.get_history(limit=100)
            self._render_table(data)
            self._render_charts(data)
        except Exception as exc:  # pragma: no cover - UI fallback
            QMessageBox.critical(self, "History Error", f"Unable to load history: {exc}")

    def _render_table(self, rows):
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                str(row.get("timestamp", "")),
                f"{row.get('soc_percent', 0.0):.1f}",
                f"{row.get('pack_voltage', 0.0):.2f}",
                f"{row.get('pack_current', 0.0):.2f}",
                f"{row.get('temperature', 0.0):.1f}",
                str(row.get("battery_status", "")),
                str(row.get("grid_status", "")),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_index, col, item)
        self.table.scrollToBottom()

    def _render_charts(self, rows):
        if not rows:
            for chart in (self.soc_chart, self.voltage_chart, self.current_chart, self.temperature_chart):
                chart.update_chart(values=[])
            return

        self.soc_chart.update_chart(values=[float(r.get("soc_percent", 0.0)) for r in rows])
        self.voltage_chart.update_chart(values=[float(r.get("pack_voltage", 0.0)) for r in rows])
        self.current_chart.update_chart(values=[float(r.get("pack_current", 0.0)) for r in rows])
        self.temperature_chart.update_chart(values=[float(r.get("temperature", 0.0)) for r in rows])