from PySide6.QtWidgets import QMainWindow, QTabWidget

from .pcp_factory import create_pcp_main_window


APP_TITLE = "Pearson Quote Pro"


class QuoteProWindow(QMainWindow):
    """Host three identical PCP windows for CTO, ETO, and Reactive tabs."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1400, 900)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self._pcp_cto = create_pcp_main_window()
        self._pcp_eto = create_pcp_main_window()
        self._pcp_rx = create_pcp_main_window()

        self.tabs.addTab(self._pcp_cto, "CTO")
        self.tabs.addTab(self._pcp_eto, "ETO")
        self.tabs.addTab(self._pcp_rx, "Reactive")

        self.setCentralWidget(self.tabs)
