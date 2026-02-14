from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from legacy_pcp.pcp_v1_1 import MainWindow as PCPMainWindow


APP_TITLE = "Pearson Quote Pro"


class QuoteProWindow(QMainWindow):
    """
    Host three full CommissioningPro instances in one shell window.

    - CTO, ETO, Reactive are top selectable buttons.
    - Each mode is a separate unmodified PCP MainWindow instance.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1600, 1000)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        button_row = QWidget()
        button_row.setObjectName("modeRow")
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(12, 10, 12, 10)
        button_layout.setSpacing(8)

        self.btn_cto = self._make_mode_button("CTO", 0)
        self.btn_eto = self._make_mode_button("ETO", 1)
        self.btn_rx = self._make_mode_button("Reactive", 2)

        button_layout.addWidget(self.btn_cto)
        button_layout.addWidget(self.btn_eto)
        button_layout.addWidget(self.btn_rx)
        button_layout.addStretch(1)

        self.stack = QStackedWidget()

        self._pcp_cto = PCPMainWindow()
        self._pcp_eto = PCPMainWindow()
        self._pcp_rx = PCPMainWindow()

        self.stack.addWidget(self._embed(self._pcp_cto))
        self.stack.addWidget(self._embed(self._pcp_eto))
        self.stack.addWidget(self._embed(self._pcp_rx))

        root_layout.addWidget(button_row)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        self._set_mode(0)

    def _make_mode_button(self, label: str, index: int) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.clicked.connect(lambda _=False, i=index: self._set_mode(i))
        return btn

    def _set_mode(self, index: int):
        self.stack.setCurrentIndex(index)
        self.btn_cto.setChecked(index == 0)
        self.btn_eto.setChecked(index == 1)
        self.btn_rx.setChecked(index == 2)

        active = "#F05A28"
        inactive = "#E2E8F0"
        text_active = "#0B1B2A"
        text_inactive = "#334155"

        self.btn_cto.setStyleSheet(self._mode_btn_css(self.btn_cto.isChecked(), active, inactive, text_active, text_inactive))
        self.btn_eto.setStyleSheet(self._mode_btn_css(self.btn_eto.isChecked(), active, inactive, text_active, text_inactive))
        self.btn_rx.setStyleSheet(self._mode_btn_css(self.btn_rx.isChecked(), active, inactive, text_active, text_inactive))

    @staticmethod
    def _mode_btn_css(is_active: bool, active: str, inactive: str, text_active: str, text_inactive: str) -> str:
        bg = active if is_active else inactive
        fg = text_active if is_active else text_inactive
        return (
            "QPushButton {"
            f"background: {bg};"
            f"color: {fg};"
            "border: none;"
            "padding: 8px 14px;"
            "border-radius: 8px;"
            "font-weight: 800;"
            "}"
        )

    @staticmethod
    def _embed(pcp_window) -> QWidget:
        content = pcp_window.takeCentralWidget()
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        content.setParent(wrapper)
        layout.addWidget(content)
        return wrapper
