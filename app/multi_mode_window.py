from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from legacy_pcp.pcp_v1_1 import MainWindow as PCPMainWindow


APP_TITLE = "Pearson Quote Pro"
MODE_LABELS = ("CTO", "ETO", "Reactive")


class MultiModeWindow(QMainWindow):
    """Single shell window hosting three full CommissioningPro instances."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1600, 1000)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        button_row = QWidget()
        button_row_layout = QHBoxLayout(button_row)
        button_row_layout.setContentsMargins(12, 10, 12, 10)
        button_row_layout.setSpacing(8)

        self.stack = QStackedWidget()
        self.buttons: list[QPushButton] = []
        self._pcp_instances: list[PCPMainWindow] = []

        for index, label in enumerate(MODE_LABELS):
            button = QPushButton(label)
            button.setCheckable(True)
            button.clicked.connect(lambda _=False, i=index: self._set_mode(i))
            self.buttons.append(button)
            button_row_layout.addWidget(button)

            pcp_window = PCPMainWindow()
            self._pcp_instances.append(pcp_window)
            self.stack.addWidget(self._embed(pcp_window))

        button_row_layout.addStretch(1)
        root_layout.addWidget(button_row)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        self._set_mode(0)

    def _set_mode(self, index: int):
        self.stack.setCurrentIndex(index)
        for button_index, button in enumerate(self.buttons):
            button.setChecked(button_index == index)

    @staticmethod
    def _embed(pcp_window: PCPMainWindow) -> QWidget:
        content = pcp_window.takeCentralWidget()
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        content.setParent(wrapper)
        layout.addWidget(content)
        return wrapper
