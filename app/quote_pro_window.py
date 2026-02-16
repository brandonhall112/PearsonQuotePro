from PySide6.QtWidgets import QMainWindow, QTabWidget

from legacy_pcp.pcp_v1_1 import MainWindow as PCPMainWindow


APP_TITLE = "Pearson Quote Pro"


class QuoteProWindow(QMainWindow):
    """Host three identical PCP windows for CTO, ETO, and Reactive tabs."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1400, 900)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self._pcp_cto = PCPMainWindow()
        self._pcp_eto = PCPMainWindow()
        self._pcp_rx = PCPMainWindow()

        self.tabs.addTab(self._pcp_cto, "CTO")
        self.tabs.addTab(self._pcp_eto, "ETO")
        self.tabs.addTab(self._pcp_rx, "Reactive")

        self.setCentralWidget(self.tabs)
