from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt


class InfoCard(QWidget):

    def __init__(self, title, value):
        super().__init__()

        self.setMinimumSize(220, 120)

        self.setStyleSheet("""
            QWidget{
                background:#1F2937;
                border-radius:15px;
            }

            QLabel{
                color:white;
                border:none;
            }
        """)

        layout = QVBoxLayout(self)

        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignCenter)

        self.title.setStyleSheet("""
            font-size:13px;
            color:#9CA3AF;
        """)

        self.value = QLabel(value)
        self.value.setAlignment(Qt.AlignCenter)

        self.value.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
            color:#14B8A6;
        """)

        layout.addStretch()
        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addStretch()

    def update_value(self, value):
        self.value.setText(str(value))