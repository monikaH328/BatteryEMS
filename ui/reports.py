from pathlib import Path

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

import config
import db


class ReportsPage(QWidget):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.setStyleSheet("""
            QWidget { background: #111827; color: white; }
            QLabel { color: white; }
            QPushButton { background: #1F2937; border: 1px solid #374151; border-radius: 8px; color: white; padding: 10px 18px; }
            QPushButton:hover { background: #0F766E; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Reports")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)

        self.daily_button = QPushButton("Generate Daily Report")
        self.daily_button.clicked.connect(self.generate_daily_report)
        layout.addWidget(self.daily_button)

        self.battery_button = QPushButton("Generate Battery Report")
        self.battery_button.clicked.connect(self.generate_battery_report)
        layout.addWidget(self.battery_button)

        self.fault_button = QPushButton("Generate Fault Report")
        self.fault_button.clicked.connect(self.generate_fault_report)
        layout.addWidget(self.fault_button)

        self.message = QLabel("Reports will be saved to the project reports directory.")
        self.message.setWordWrap(True)
        self.message.setStyleSheet("background: #1F2937; border: 1px solid #374151; border-radius: 8px; padding: 12px;")
        layout.addWidget(self.message)

    def _ensured_reports_dir(self):
        path = Path(config.REPORTS_PATH)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _show_success(self, file_path):
        self.message.setText(f"Report generated successfully: {file_path}")
        QMessageBox.information(self, "Report Generated", f"Generated PDF: {file_path}")

    def _show_error(self, message):
        self.message.setText(f"Error generating report: {message}")
        QMessageBox.critical(self, "Report Error", message)

    def _safe_history(self):
        try:
            return db.get_recent_readings(limit=500)
        except Exception:
            return []

    def generate_daily_report(self):
        try:
            report_dir = self._ensured_reports_dir()
            stats = db.get_statistics() if hasattr(db, "get_statistics") else {}
            rows = self._safe_history()
            total = len(rows)
            avg_soc = stats.get("avg_soc", sum(r.get("soc_percent", 0.0) for r in rows) / total if total else 0.0)
            min_soc = stats.get("min_soc", min((r.get("soc_percent", 0.0) for r in rows), default=0.0))
            max_soc = stats.get("max_soc", max((r.get("soc_percent", 0.0) for r in rows), default=0.0))
            avg_voltage = stats.get("avg_voltage", sum(r.get("pack_voltage", 0.0) for r in rows) / total if total else 0.0)
            avg_current = stats.get("avg_current", sum(r.get("pack_current", 0.0) for r in rows) / total if total else 0.0)
            avg_temp = stats.get("avg_temperature", sum(r.get("temperature", 0.0) for r in rows) / total if total else 0.0)
            fault_count = len(db.get_fault_records(limit=500)) if hasattr(db, "get_fault_records") else 0
            file_path = report_dir / "daily_report.pdf"
            doc = SimpleDocTemplate(str(file_path), pagesize=letter)
            styles = getSampleStyleSheet()
            story = [Paragraph("BatteryEMS Report", styles["Title"]), Spacer(1, 12),
                     Paragraph(f"Date: {db.get_db_timestamp() if hasattr(db, 'get_db_timestamp') else 'N/A'}", styles["Normal"]),
                     Paragraph(f"Total readings: {total}", styles["Normal"]),
                     Paragraph(f"Average SOC: {float(avg_soc):.1f}%", styles["Normal"]),
                     Paragraph(f"Minimum SOC: {float(min_soc):.1f}%", styles["Normal"]),
                     Paragraph(f"Maximum SOC: {float(max_soc):.1f}%", styles["Normal"]),
                     Paragraph(f"Average voltage: {float(avg_voltage):.2f} V", styles["Normal"]),
                     Paragraph(f"Average current: {float(avg_current):.2f} A", styles["Normal"]),
                     Paragraph(f"Average temperature: {float(avg_temp):.1f} °C", styles["Normal"]),
                     Paragraph(f"Fault count: {fault_count}", styles["Normal"]),
                     Paragraph("Grid UP/DOWN information: see current simulation status.", styles["Normal"])]
            doc.build(story)
            self._show_success(str(file_path))
        except Exception as exc:
            self._show_error(str(exc))

    def generate_battery_report(self):
        try:
            data = self.controller.get_live_data() if self.controller else {"soc": 0.0, "voltage": 0.0, "current": 0.0, "temperature": 0.0, "cells": [0.0] * 4, "status": "OK", "balancing": []}
            report_dir = self._ensured_reports_dir()
            file_path = report_dir / "battery_report.pdf"
            doc = SimpleDocTemplate(str(file_path), pagesize=letter)
            styles = getSampleStyleSheet()
            story = [Paragraph("Battery Report", styles["Title"]), Spacer(1, 12),
                     Paragraph(f"Current SOC: {float(data.get('bms', {}).get('soc_percent', 0.0)):.1f}%", styles["Normal"]),
                     Paragraph(f"Voltage: {float(data.get('bms', {}).get('pack_voltage', 0.0)):.2f} V", styles["Normal"]),
                     Paragraph(f"Current: {float(data.get('bms', {}).get('current_a', 0.0)):.2f} A", styles["Normal"]),
                     Paragraph(f"Temperature: {float(data.get('bms', {}).get('temperature_c', 0.0)):.1f} °C", styles["Normal"]),
                     Paragraph(f"Battery status: {data.get('bms', {}).get('status', 'OK')}", styles["Normal"]),
                     Paragraph(f"Balancing status: {data.get('bms', {}).get('balancing_cells', []) or 'None'}", styles["Normal"]),
                     Spacer(1, 10)]
            cell_values = data.get("bms", {}).get("cell_voltages", [0.0] * 4)
            cell_table = [[f"Cell {idx + 1}", f"{float(v):.3f} V"] for idx, v in enumerate(cell_values[:4])]
            story.append(Table(cell_table, colWidths=[120, 200]))
            story.append(Spacer(1, 12))
            if len(cell_values) >= 4:
                spread = max(cell_values) - min(cell_values)
                story.append(Paragraph(f"Cell spread: {spread:.3f} V", styles["Normal"]))
            doc.build(story)
            self._show_success(str(file_path))
        except Exception as exc:
            self._show_error(str(exc))

    def generate_fault_report(self):
        try:
            report_dir = self._ensured_reports_dir()
            rows = db.get_fault_records(limit=100)
            file_path = report_dir / "fault_report.pdf"
            doc = SimpleDocTemplate(str(file_path), pagesize=letter)
            styles = getSampleStyleSheet()
            story = [Paragraph("Fault Report", styles["Title"]), Spacer(1, 12)]
            if not rows:
                story.append(Paragraph("No fault records available.", styles["Normal"]))
            else:
                rows_data = [["Timestamp", "Battery Status", "Relevant Readings"]]
                for row in rows:
                    rows_data.append([
                        str(row.get("timestamp", "")),
                        str(row.get("battery_status", "")),
                        f"SOC {row.get('soc_percent', 0.0):.1f}% | Voltage {row.get('pack_voltage', 0.0):.2f} V | Temp {row.get('temperature', 0.0):.1f} °C",
                    ])
                story.append(Table(rows_data, colWidths=[140, 120, 270]))
            doc.build(story)
            self._show_success(str(file_path))
        except Exception as exc:
            self._show_error(str(exc))