from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QComboBox,
)


class DeviceManagerPage(QWidget):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.setStyleSheet("""
            QWidget { background: #111827; color: white; }
            QLabel { color: white; }
            QGroupBox { border: 1px solid #374151; border-radius: 12px; margin-top: 14px; padding-top: 12px; background: #111827; }
            QPushButton { background: #1F2937; border: 1px solid #374151; border-radius: 8px; color: white; padding: 8px 16px; }
            QPushButton:hover { background: #0F766E; }
            QComboBox { background: #1F2937; border: 1px solid #374151; color: white; padding: 6px; border-radius: 8px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        title = QLabel("Device Manager")
        title.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(title)

        self.device_box = QGroupBox("Connection")
        device_layout = QVBoxLayout(self.device_box)

        self.device_type = QLabel("Current Device: Simulator")
        self.connection_status = QLabel("Connection: Connected")
        self.device_type.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.connection_status.setStyleSheet("font-size: 16px; color: #6EE7B7;")
        device_layout.addWidget(self.device_type)
        device_layout.addWidget(self.connection_status)

        select_row = QHBoxLayout()
        self.device_selector = QComboBox()
        self.device_selector.addItems(["Simulator", "ESP32"])
        select_row.addWidget(QLabel("Device type:"))
        select_row.addWidget(self.device_selector)
        device_layout.addLayout(select_row)

        buttons = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.refresh_btn = QPushButton("Refresh")
        buttons.addWidget(self.connect_btn)
        buttons.addWidget(self.disconnect_btn)
        buttons.addWidget(self.refresh_btn)
        device_layout.addLayout(buttons)

        self.connect_btn.clicked.connect(self.connect_selected_device)
        self.disconnect_btn.clicked.connect(self.disconnect_selected_device)
        self.refresh_btn.clicked.connect(self.refresh_status)
        self.device_selector.currentTextChanged.connect(self.change_device)

        layout.addWidget(self.device_box)
        self.refresh_status()

    def change_device(self, value):
        if self.controller is None:
            return
        if value == "ESP32":
            self.controller.set_active_device("esp32")
        else:
            self.controller.set_active_device("simulator")
        self.refresh_status()

    def connect_selected_device(self):
        if self.controller is not None:
            self.controller.connect_device()
        self.refresh_status()

    def disconnect_selected_device(self):
        if self.controller is not None:
            self.controller.disconnect_device()
        self.refresh_status()

    def refresh_status(self):
        if self.controller is None:
            return
        status = self.controller.get_device_status()
        device = status.get("device", "Simulator")
        connection = status.get("connection", "Connected")
        self.device_type.setText(f"Current Device: {device}")
        self.connection_status.setText(f"Connection: {connection}")
        self.connection_status.setStyleSheet("font-size: 16px; color: #6EE7B7;" if "Connected" in connection or "Ready" in connection else "font-size: 16px; color: #FCA5A5;")
        if device == "ESP32":
            self.device_selector.setCurrentText("ESP32")
        else:
            self.device_selector.setCurrentText("Simulator")
