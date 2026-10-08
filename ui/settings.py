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
        self.num_cells = QSpinBox(); self.num_cells.setRange(1, 500); self.num_cells.setValue(int(config.NUM_CELLS))
        self.cell_ov = QDoubleSpinBox(); self.cell_ov.setRange(3.0, 5.0); self.cell_ov.setSingleStep(0.01); self.cell_ov.setValue(float(config.CELL_OVERVOLTAGE_THRESHOLD))
        self.cell_uv = QDoubleSpinBox(); self.cell_uv.setRange(1.0, 4.0); self.cell_uv.setSingleStep(0.01); self.cell_uv.setValue(float(config.CELL_UNDERVOLTAGE_THRESHOLD))
        self.pack_oc = QDoubleSpinBox(); self.pack_oc.setRange(1.0, 20.0); self.pack_oc.setSingleStep(0.1); self.pack_oc.setValue(float(config.PACK_OVERCURRENT_THRESHOLD_A))
        self.pack_ot = QDoubleSpinBox(); self.pack_ot.setRange(20.0, 100.0); self.pack_ot.setSingleStep(0.5); self.pack_ot.setValue(float(config.PACK_OVERTEMP_THRESHOLD_C))
        self.imbalance = QDoubleSpinBox(); self.imbalance.setRange(0.01, 1.0); self.imbalance.setSingleStep(0.01); self.imbalance.setValue(float(config.IMBALANCE_TRIGGER_V))
        self.auto_start = QComboBox(); self.auto_start.addItems(["True", "False"]); self.auto_start.setCurrentText(str(getattr(config, "START_SIMULATOR_AUTOMATICALLY", True)))
        self.theme = QComboBox(); self.theme.addItems(["Dark", "Light"]); self.theme.setCurrentText(str(getattr(config, "THEME", "Dark")))
        self.logging = QComboBox(); self.logging.addItems(["True", "False"]); self.logging.setCurrentText(str(getattr(config, "DATA_LOGGING_ENABLED", True)))

        for label, widget in [
            ("Number of cells", self.num_cells),
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
            new_values = {
                "NUM_CELLS": int(self.num_cells.value()),
                "UPDATE_INTERVAL": float(self.update_interval.value()),
                "BATTERY_CAPACITY_AH": float(self.battery_capacity.value()),
                "INITIAL_SOC_PERCENT": float(self.initial_soc.value()),
                "CELL_OVERVOLTAGE_THRESHOLD": float(self.cell_ov.value()),
                "CELL_UNDERVOLTAGE_THRESHOLD": float(self.cell_uv.value()),
                "PACK_OVERCURRENT_THRESHOLD_A": float(self.pack_oc.value()),
                "PACK_OVERTEMP_THRESHOLD_C": float(self.pack_ot.value()),
                "IMBALANCE_TRIGGER_V": float(self.imbalance.value()),
                "START_SIMULATOR_AUTOMATICALLY": self.auto_start.currentText() == "True",
                "DATA_LOGGING_ENABLED": self.logging.currentText() == "True",
            }

            cells_changed = int(self.num_cells.value()) != int(config.NUM_CELLS)

            for key, value in new_values.items():
                setattr(config, key, value)
            config.THEME = self.theme.currentText()

            self._persist_to_config_file(new_values, theme=self.theme.currentText())

            if cells_changed:
                QMessageBox.information(
                    self, "Restart Required",
                    "Number of cells changed. This requires restarting the application "
                    "to take effect -- the simulated/real battery pack is built once at startup."
                )
            else:
                QMessageBox.information(self, "Settings Applied", "Configuration updated and saved.")
        except Exception as exc:
            QMessageBox.critical(self, "Settings Error", f"Invalid configuration: {exc}")

    def _persist_to_config_file(self, values, theme=None):
        """Writes the new values into config.py on disk so they survive a restart."""
        with open("config.py") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            stripped = line.strip()
            for key, value in values.items():
                if stripped.startswith(f"{key} ="):
                    lines[i] = f"{key} = {value}\n"
            if theme is not None and stripped.startswith("THEME ="):
                lines[i] = f'THEME = "{theme}"\n'

        with open("config.py", "w") as f:
            f.writelines(lines)

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