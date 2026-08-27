# ui/theme.py

APP_STYLE = """
QMainWindow {
    background-color: #111827;
}

QWidget {
    background-color: #111827;
    color: white;
    font-family: Segoe UI;
    font-size: 12pt;
}

QListWidget {
    background-color: #1F2937;
    border: none;
    padding: 10px;
    color: white;
    font-size: 12pt;
}

QListWidget::item {
    padding: 12px;
    border-radius: 8px;
    margin: 4px;
}

QListWidget::item:selected {
    background-color: #14B8A6;
    color: white;
    font-weight: bold;
}

QListWidget::item:hover {
    background-color: #374151;
}

QStatusBar {
    background-color: #1F2937;
    color: white;
}

QLabel {
    color: white;
}
"""