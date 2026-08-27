from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QStackedWidget,
    QStatusBar,
)

from backend.controller import BatteryController
from ui.about import AboutPage
from ui.dashboard import DashboardPage
from ui.device_manager import DeviceManagerPage
from ui.history import HistoryPage
from ui.live_monitor import LiveMonitorPage
from ui.reports import ReportsPage
from ui.settings import SettingsPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.controller = BatteryController()
        self.setWindowTitle("BatteryEMS v1.0")
        self.resize(1400, 850)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.addItems([
            "🏠 Dashboard",
            "📈 Live Monitor",
            "🕐 History",
            "📄 Reports",
            "⚙ Settings",
            "🔌 Device Manager",
            "ℹ About",
        ])
        layout.addWidget(self.sidebar)

        self.pages = QStackedWidget()

        self.dashboard = DashboardPage(self.controller)
        self.live_monitor = LiveMonitorPage(self.controller)
        self.history = HistoryPage(self.controller)
        self.reports = ReportsPage(self.controller)
        self.settings = SettingsPage(self.controller)
        self.device = DeviceManagerPage(self.controller)
        self.about = AboutPage()

        for page in (self.dashboard, self.live_monitor, self.history, self.reports, self.settings, self.device, self.about):
            self.pages.addWidget(page)

        layout.addWidget(self.pages)

        self.sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        status = QStatusBar()
        status.showMessage("Status : Ready")
        self.setStatusBar(status)

        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self._refresh_all)
        self.tick_timer.start(1000)

    def _refresh_all(self):
        self.controller.update()
        for page in (self.dashboard, self.live_monitor, self.history, self.reports, self.settings, self.device):
            if hasattr(page, "refresh"):
                try:
                    page.refresh()
                except Exception:
                    pass

        if hasattr(self.about, "refresh"):
            try:
                self.about.refresh()
            except Exception:
                pass