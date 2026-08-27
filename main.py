import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import APP_STYLE

app = QApplication(sys.argv)

# Apply global theme
app.setStyleSheet(APP_STYLE)

window = MainWindow()
window.show()

sys.exit(app.exec())