from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout
from legacy_pcp.pcp_v1_1 import MainWindow as PCPMainWindow


APP_TITLE = "Pearson Quote Pro"


class QuoteProWindow(QMainWindow):
    """
    Start-over baseline:
    - Three identical copies of PCP embedded in tabs.
    - Tabs labeled: CTO, ETO, Reactive.
    - NO extra theme/styles so each tab looks like PCP.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1400, 900)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Create 3 independent PCP instances (identical baseline).
        self._pcp_cto = PCPMainWindow()
        self._pcp_eto = PCPMainWindow()
        self._pcp_rx = PCPMainWindow()

        # Embed each PCP's central widget into a tab.
        self.tabs.addTab(self._embed_pcp(self._pcp_cto), "CTO")
        self.tabs.addTab(self._embed_pcp(self._pcp_eto), "ETO")
        self.tabs.addTab(self._embed_pcp(self._pcp_rx), "Reactive")

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)
        self.setCentralWidget(root)

    @staticmethod
    def _embed_pcp(pcp_window: PCPMainWindow) -> QWidget:
        # Take the PCP central widget and re-parent into our tab container.
        w = pcp_window.takeCentralWidget()
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(0, 0, 0, 0)
        w.setParent(tab)
        l.addWidget(w)
        return tab
