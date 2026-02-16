from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from legacy_pcp.pcp_v1_1 import MainWindow as PCPMainWindow


APP_TITLE = "Pearson Quote Pro"


class QuoteProWindow(QMainWindow):
    """Single shell window hosting three full CommissioningPro instances."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1600, 1000)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 10, 12, 10)
        row_layout.setSpacing(8)

        self.stack = QStackedWidget()
        self.buttons: list[QPushButton] = []
        self._pcp_instances: list[PCPMainWindow] = []

        for idx, label in enumerate(("CTO", "ETO", "Reactive")):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, i=idx: self._set_mode(i))
            self.buttons.append(btn)
            row_layout.addWidget(btn)

            pcp = PCPMainWindow()
            self._pcp_instances.append(pcp)
            self.stack.addWidget(self._embed(pcp))

        row_layout.addStretch(1)
        root_layout.addWidget(row)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        self._set_mode(0)

    def _set_mode(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)

    @staticmethod
    def _embed(pcp_window) -> QWidget:
        content = pcp_window.takeCentralWidget()
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        content.setParent(wrapper)
        layout.addWidget(content)
        return wrapper
