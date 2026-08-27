from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ChartWidget(QWidget):

    def __init__(self, title):
        super().__init__()

        self.figure = Figure(figsize=(5, 2.5))
        self.figure.patch.set_alpha(0)
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self.title = title
        self.x = []
        self.y = []
        self._setup_axis()

    def _setup_axis(self):
        self.ax.set_title(self.title, fontsize=12, fontweight="bold")
        self.ax.set_facecolor("#1F2937")
        self.ax.tick_params(axis="both", colors="white", labelsize=9)
        self.ax.set_xlabel("Samples", color="white")
        self.ax.set_ylabel(self.title, color="white")
        for spine in self.ax.spines.values():
            spine.set_color("#374151")
        self.ax.grid(True, alpha=0.2)
        self.figure.tight_layout()

    def update_chart(self, value=None, values=None):
        if values is not None:
            self.x = list(range(len(values)))
            self.y = [float(v) for v in values]
        else:
            if value is None:
                return
            self.x.append(len(self.x) + 1)
            self.y.append(float(value))
            if len(self.x) > 60:
                self.x = self.x[-60:]
                self.y = self.y[-60:]

        self.ax.clear()
        self.ax.plot(self.x, self.y, linewidth=2, color="#14B8A6")
        self._setup_axis()
        self.canvas.draw_idle()
