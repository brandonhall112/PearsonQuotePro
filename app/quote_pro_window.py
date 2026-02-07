from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout

from legacy_pcp.pcp_v1_1 import MainWindow as PCPMainWindow
from app.reactive_pcp import ReactiveMainWindow


APP_TITLE = "Pearson Quote Pro"


class QuoteProWindow(QMainWindow):
    """
    Baseline:
    - CTO + ETO: identical PCP
    - Reactive: identical PCP look/feel, with Machine Configuration repurposed to Resources
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1400, 900)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self._pcp_cto = PCPMainWindow()
        self._pcp_eto = PCPMainWindow()
        self._pcp_rx = ReactiveMainWindow()

        self.tabs.addTab(self._embed(self._pcp_cto), "CTO")
        self.tabs.addTab(self._embed(self._pcp_eto), "ETO")
        self.tabs.addTab(self._embed(self._pcp_rx), "Reactive")

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)
        self.setCentralWidget(root)

    @staticmethod
    def _embed(pcp_window) -> QWidget:
        w = pcp_window.takeCentralWidget()
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(0, 0, 0, 0)
        w.setParent(tab)
        l.addWidget(w)
        return tab
