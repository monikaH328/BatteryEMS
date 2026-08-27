from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFormLayout, QDoubleSpinBox, QSpinBox, QComboBox, QPushButton, QMessageBox

import config


class SettingsPage(QWidget):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.setStyleSheet("""
            QWidget { background: #111827; color: white; }
            QLabel { color: white; }
            QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox { background: #1F2937; color: white; border: 1px solid #374151; border-radius: 8px; padding: 6px; }
            QPushButton { background: #1F2937; border: 1px solid #374151; border-radius: 8px; color: white; padding: 10px 18px; }
            QPushButton:hover { background: #0F766E; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)

        form = QFormLayout()
        self.update_interval = QDoubleSpinBox(); self.update_interval.setRange(0.2, 10.0); self.update_interval.setSingleStep(0.1); self.update_interval.setValue(float(getattr(config, "UPDATE_INTERVAL", 1.0)))
        self.battery_capacity = QDoubleSpinBox(); self.battery_capacity.setRange(0.5, 100.0); self.battery_capacity.setSingleStep(0.1); self.battery_capacity.setValue(float(getattr(config, "BATTERY_CAPACITY_AH", config.RATED_CAPACITY_AH)))
        self.initial_soc = QDoubleSpinBox(); self.initial_soc.setRange(0.0, 100.0); self.initial_soc.setSingleStep(1.0); self.initial_soc.setValue(float(getattr(config, "INITIAL_SOC_PERCENT", 60.0)))
        self.cell_ov = QDoubleSpinBox(); self.cell_ov.setRange(3.0, 5.0); self.cell_ov.setSingleStep(0.01); self.cell_ov.setValue(float(config.CELL_OVERVOLTAGE_THRESHOLD))
        self.cell_uv = QDoubleSpinBox(); self.cell_uv.setRange(1.0, 4.0); self.cell_uv.setSingleStep(0.01); self.cell_uv.setValue(float(config.CELL_UNDERVOLTAGE_THRESHOLD))
        self.pack_oc = QDoubleSpinBox(); self.pack_oc.setRange(1.0, 20.0); self.pack_oc.setSingleStep(0.1); self.pack_oc.setValue(float(config.PACK_OVERCURRENT_THRESHOLD_A))
        self.pack_ot = QDoubleSpinBox(); self.pack_ot.setRange(20.0, 100.0); self.pack_ot.setSingleStep(0.5); self.pack_ot.setValue(float(config.PACK_OVERTEMP_THRESHOLD_C))
        self.imbalance = QDoubleSpinBox(); self.imbalance.setRange(0.01, 1.0); self.imbalance.setSingleStep(0.01); self.imbalance.setValue(float(config.IMBALANCE_TRIGGER_V))
        self.auto_start = QComboBox(); self.auto_start.addItems(["True", "False"]); self.auto_start.setCurrentText(str(getattr(config, "START_SIMULATOR_AUTOMATICALLY", True)))
        self.theme = QComboBox(); self.theme.addItems(["Dark", "Light"]); self.theme.setCurrentText(str(getattr(config, "THEME", "Dark")))
        self.logging = QComboBox(); self.logging.addItems(["True", "False"]); self.logging.setCurrentText(str(getattr(config, "DATA_LOGGING_ENABLED", True)))

        for label, widget in [
            ("Update interval", self.update_interval),
            ("Battery capacity", self.battery_capacity),
            ("Initial SOC", self.initial_soc),
            ("Cell overvoltage", self.cell_ov),
            ("Cell undervoltage", self.cell_uv),
            ("Pack overcurrent", self.pack_oc),
            ("Pack overtemperature", self.pack_ot),
            ("Cell imbalance threshold", self.imbalance),
            ("Start simulator automatically", self.auto_start),
            ("Theme", self.theme),
            ("Data logging enabled", self.logging),
        ]:
            form.addRow(label, widget)
        layout.addLayout(form)

        btn_layout = QVBoxLayout()
        self.apply_button = QPushButton("Apply")
        self.reset_button = QPushButton("Reset Defaults")
        self.apply_button.clicked.connect(self.apply_settings)
        self.reset_button.clicked.connect(self.reset_defaults)
        btn_layout.addWidget(self.apply_button)
        btn_layout.addWidget(self.reset_button)
        layout.addLayout(btn_layout)

        self.info = QLabel("Startup configuration: changes apply on next launch or restart; runtime protection values remain in the core BMS logic.")
        self.info.setWordWrap(True)
        self.info.setStyleSheet("background: #1F2937; border: 1px solid #374151; border-radius: 8px; padding: 10px;")
        layout.addWidget(self.info)

    def apply_settings(self):
        try:
            config.UPDATE_INTERVAL = float(self.update_interval.value())
            config.BATTERY_CAPACITY_AH = float(self.battery_capacity.value())
            config.INITIAL_SOC_PERCENT = float(self.initial_soc.value())
            config.CELL_OVERVOLTAGE_THRESHOLD = float(self.cell_ov.value())
            config.CELL_UNDERVOLTAGE_THRESHOLD = float(self.cell_uv.value())
            config.PACK_OVERCURRENT_THRESHOLD_A = float(self.pack_oc.value())
            config.PACK_OVERTEMP_THRESHOLD_C = float(self.pack_ot.value())
            config.IMBALANCE_TRIGGER_V = float(self.imbalance.value())
            config.START_SIMULATOR_AUTOMATICALLY = self.auto_start.currentText() == "True"
            config.THEME = self.theme.currentText()
            config.DATA_LOGGING_ENABLED = self.logging.currentText() == "True"
            QMessageBox.information(self, "Settings Applied", "Configuration updated successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Settings Error", f"Invalid configuration: {exc}")

    def reset_defaults(self):
        self.update_interval.setValue(float(getattr(config, "UPDATE_INTERVAL", 1.0)))
        self.battery_capacity.setValue(float(getattr(config, "BATTERY_CAPACITY_AH", config.RATED_CAPACITY_AH)))
        self.initial_soc.setValue(float(getattr(config, "INITIAL_SOC_PERCENT", 60.0)))
        self.cell_ov.setValue(float(config.CELL_OVERVOLTAGE_THRESHOLD))
        self.cell_uv.setValue(float(config.CELL_UNDERVOLTAGE_THRESHOLD))
        self.pack_oc.setValue(float(config.PACK_OVERCURRENT_THRESHOLD_A))
        self.pack_ot.setValue(float(config.PACK_OVERTEMP_THRESHOLD_C))
        self.imbalance.setValue(float(config.IMBALANCE_TRIGGER_V))
        self.auto_start.setCurrentText(str(getattr(config, "START_SIMULATOR_AUTOMATICALLY", True)))
        self.theme.setCurrentText(str(getattr(config, "THEME", "Dark")))
        self.logging.setCurrentText(str(getattr(config, "DATA_LOGGING_ENABLED", True)))
        QMessageBox.information(self, "Defaults Restored", "Default values restored.")

    def refresh(self):
        pass