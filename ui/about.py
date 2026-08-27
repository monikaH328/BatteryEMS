from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt


class AboutPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget { background: #111827; color: white; }
            QLabel { color: white; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("BatteryEMS")
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Battery Energy Management System")
        subtitle.setStyleSheet("font-size: 18px; color: #9CA3AF;")
        layout.addWidget(subtitle)

        version = QLabel("Version: 1.0")
        version.setStyleSheet("font-size: 16px; margin-top: 8px;")
        layout.addWidget(version)

        features = QLabel(
            "Features:\n"
            "• Battery monitoring\n"
            "• BMS protection\n"
            "• SOC estimation\n"
            "• Cell monitoring\n"
            "• Cell balancing\n"
            "• Fault detection\n"
            "• EMS control\n"
            "• Grid monitoring\n"
            "• Historical data\n"
            "• PDF reporting\n"
            "• ESP32 integration framework"
        )
        features.setStyleSheet("background: #1F2937; border-radius: 12px; padding: 14px; line-height: 1.8;")
        layout.addWidget(features)

        tech = QLabel(
            "Technology:\n"
            "Python\n"
            "PySide6\n"
            "SQLite\n"
            "PyQtGraph\n"
            "Flask\n"
            "Socket.IO\n"
            "ReportLab"
        )
        tech.setStyleSheet("background: #1F2937; border-radius: 12px; padding: 14px; line-height: 1.8;")
        layout.addWidget(tech)

        arch = QLabel(
            "Architecture:\n\n"
            "Battery Simulator / ESP32\n"
            "        ↓\n"
            "BMS Core\n"
            "        ↓\n"
            "EMS Core\n"
            "        ↓\n"
            "Controller\n"
            "        ↓\n"
            "Desktop UI / Web Dashboard\n"
            "        ↓\n"
            "SQLite Database"
        )
        arch.setStyleSheet("background: #1F2937; border-radius: 12px; padding: 14px; line-height: 1.8;")
        layout.addWidget(arch)

        layout.addStretch()