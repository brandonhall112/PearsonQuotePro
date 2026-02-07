import os
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QTextEdit, QTableWidget, QTableWidgetItem, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt

from legacy_pcp.pcp_v1_1 import MainWindow as PCPMainWindow, resolve_excel_path, ExcelData
from app.tm_quote_renderer import build_tm_quote_html, write_html_temp_and_open


APP_TITLE = "Pearson Quote Pro"
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"


def qp_stylesheet() -> str:
    """
    IMPORTANT: Scope styles to Quote Pro widgets ONLY.
    Do NOT use a global QWidget selector, otherwise we override PCP's CTO styling.
    """
    blue = "#0B2E4B"
    gold = "#F05A28"
    neutral = "#64748B"
    red = "#B91C1C"

    return f"""
    /* Scope to Quote Pro root only */
    QWidget#qpRoot {{ font-family: Arial, Helvetica, sans-serif; font-size: 10pt; color: #0F172A; }}

    QFrame#qpPanel {{
        background: #FFFFFF;
        border: 1px solid #E6E8EB;
        border-radius: 12px;
        padding: 12px;
    }}
    QLabel#qpPanelTitle {{ font-size: 12pt; font-weight: 700; color: {blue}; }}
    QLabel#qpHint {{ color: {neutral}; }}

    QPushButton#qpBtn {{
        background: {gold};
        color: white;
        padding: 8px 12px;
        border-radius: 10px;
        font-weight: 700;
        min-width: 110px;
    }}
    QPushButton#qpBtn:disabled {{ background: #CBD5E1; color: #475569; }}

    QComboBox#qpQuoteType {{
        padding: 6px 10px;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        background: white;
        min-width: 220px;
    }}

    QTextEdit#qpSow {{
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        padding: 8px;
        background: white;
    }}

    QTableWidget#qpTMTable {{
        border: 1px solid #E6E8EB;
        border-radius: 12px;
        background: white;
        gridline-color: #E6E8EB;
    }}
    QHeaderView::section {{
        background: #F1F5F9;
        border: 0px;
        padding: 8px;
        font-weight: 700;
        color: #0F172A;
    }}

    QLabel#qpError {{ color: {red}; font-weight: 700; }}
    """


class QuoteProWindow(QMainWindow):
    """
    Goal:
    - CTO tab should look exactly like PCP: do NOT override PCP styling.
    - Avoid "double title bars": remove Quote Pro header frame, move controls into the tab bar corner.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1400, 900)

        self.excel_path = self._resolve_excel()
        self.data = ExcelData(self.excel_path)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.tab_common = self._build_common_tab()
        self.tab_cto = self._build_cto_tab()
        self.tab_eto = self._build_tm_tab(kind="ETO")
        self.tab_reactive = self._build_tm_tab(kind="REACTIVE", sow_required=True)

        self.tabs.addTab(self.tab_common, "Common")
        self.tabs.addTab(self.tab_cto, "CTO")
        self.tabs.addTab(self.tab_eto, "ETO")
        self.tabs.addTab(self.tab_reactive, "Reactive")

        # Controls live in the tab bar corner to avoid wasting vertical space
        self._corner = QWidget()
        corner_l = QHBoxLayout(self._corner)
        corner_l.setContentsMargins(6, 4, 6, 4)
        corner_l.setSpacing(8)

        self.quote_type = QComboBox()
        self.quote_type.setObjectName("qpQuoteType")
        self.quote_type.addItem("Commissioning (CTO)", "CTO")
        self.quote_type.addItem("Complex Install (ETO)", "ETO")
        self.quote_type.addItem("Reactive (Break/Fix)", "REACTIVE")
        self.quote_type.currentIndexChanged.connect(self._on_quote_type_changed)

        self.btn_calc = QPushButton("Calculate")
        self.btn_calc.setObjectName("qpBtn")
        self.btn_calc.clicked.connect(self.calculate_current)

        self.btn_print = QPushButton("Print / Preview")
        self.btn_print.setObjectName("qpBtn")
        self.btn_print.clicked.connect(self.print_current)

        # Small status label (kept compact)
        self.lbl_cfg = QLabel(f"Config: {self.excel_path.name}")
        self.lbl_cfg.setObjectName("qpHint")

        corner_l.addWidget(self.quote_type)
        corner_l.addWidget(self.btn_calc)
        corner_l.addWidget(self.btn_print)
        corner_l.addWidget(self.lbl_cfg)

        self.tabs.setCornerWidget(self._corner, Qt.TopRightCorner)

        # Root widget
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.addWidget(self.tabs)
        self.setCentralWidget(root)

        # Apply Quote Pro styling ONLY to Quote Pro widgets (not CTO/PCP)
        root.setObjectName("qpRoot")
        root.setStyleSheet(qp_stylesheet())

        # Start on CTO
        self._on_quote_type_changed()

    def _resolve_excel(self) -> Path:
        expected = "Tech days and quote rates.xlsx"
        p = ASSETS_DIR / expected
        if p.exists():
            return p
        rp = resolve_excel_path(expected)
        if rp is None:
            raise FileNotFoundError(f"Could not find {expected} in assets.")
        return rp

    def _build_common_tab(self) -> QWidget:
        w = QWidget()
        w.setObjectName("qpRoot")  # for scoped styling on this tab
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        panel = QFrame()
        panel.setObjectName("qpPanel")
        pl = QVBoxLayout(panel)

        t = QLabel("Common Info (used for all quote types)")
        t.setObjectName("qpPanelTitle")
        pl.addWidget(t)

        hint = QLabel("This first pass keeps Common lightweight. We’ll wire these fields into CTO + T&M outputs next increment.")
        hint.setObjectName("qpHint")
        hint.setWordWrap(True)
        pl.addWidget(hint)

        layout.addWidget(panel)
        layout.addStretch(1)
        return w

    def _build_cto_tab(self) -> QWidget:
        """
        CTO should look/act like PCP. We embed PCP's central widget.
        We intentionally do NOT apply Quote Pro scoped styling to this tab.
        """
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(0, 0, 0, 0)

        self._pcp = PCPMainWindow()
        # Reuse the already-loaded Excel config
        self._pcp.data = self.data

        central = self._pcp.takeCentralWidget()
        central.setParent(tab)
        l.addWidget(central)

        return tab

    def _build_tm_tab(self, kind: str, sow_required: bool = False) -> QWidget:
        tab = QWidget()
        tab.setObjectName("qpRoot")  # scoped styles apply here
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        panel = QFrame()
        panel.setObjectName("qpPanel")
        pl = QVBoxLayout(panel)

        title = QLabel("Time & Material")
        title.setObjectName("qpPanelTitle")
        pl.addWidget(title)

        hint = QLabel("Enter days by resource type. Rates come from the shared workbook (Service Rates).")
        hint.setObjectName("qpHint")
        hint.setWordWrap(True)
        pl.addWidget(hint)

        # T&M grid
        tbl = QTableWidget(2, 4)
        tbl.setObjectName("qpTMTable")
        tbl.setHorizontalHeaderLabels(["Resource", "Days", "Hours/Day", "Rate Key (from workbook)"])
        tbl.verticalHeader().setVisible(False)
        tbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tbl.setFixedHeight(120)

        hours_per_day = 8 if kind == "ETO" else 10
        default_rate_tech = "Tech. Regular Time"
        default_rate_eng = "Eng. Regular Time"

        def set_row(r: int, label: str, rate_key: str):
            tbl.setItem(r, 0, QTableWidgetItem(label))
            tbl.setItem(r, 1, QTableWidgetItem("0"))
            tbl.setItem(r, 2, QTableWidgetItem(str(hours_per_day)))
            tbl.setItem(r, 3, QTableWidgetItem(rate_key))

        set_row(0, "Technician", default_rate_tech)
        set_row(1, "Engineer", default_rate_eng)

        pl.addWidget(tbl)

        sow_label = QLabel("Scope of Work (SOW)")
        sow_label.setObjectName("qpPanelTitle")
        sow_label.setStyleSheet("font-size:11pt;")
        pl.addWidget(sow_label)

        sow = QTextEdit()
        sow.setObjectName("qpSow")
        sow.setPlaceholderText("Scope of Work (prints above the line item table) ...")
        sow.setFixedHeight(180)
        pl.addWidget(sow)

        err = QLabel("")
        err.setObjectName("qpError")
        err.setWordWrap(True)
        pl.addWidget(err)

        layout.addWidget(panel)
        layout.addStretch(1)

        if kind == "ETO":
            self._eto_tbl, self._eto_sow, self._eto_err = tbl, sow, err
        else:
            self._rx_tbl, self._rx_sow, self._rx_err = tbl, sow, err
            self._rx_sow_required = sow_required

        return tab

    def _on_quote_type_changed(self):
        qt = self.quote_type.currentData()

        # In CTO mode, our Calculate/Print buttons are redundant (PCP has its own).
        # Keep them enabled anyway if you want quick access; but we can disable for less confusion.
        if qt == "CTO":
            self.btn_calc.setEnabled(False)
            self.btn_print.setEnabled(False)
            self.tabs.setCurrentWidget(self.tab_cto)
        elif qt == "ETO":
            self.btn_calc.setEnabled(True)
            self.btn_print.setEnabled(True)
            self.tabs.setCurrentWidget(self.tab_eto)
        else:
            self.btn_calc.setEnabled(True)
            self.btn_print.setEnabled(True)
            self.tabs.setCurrentWidget(self.tab_reactive)

    def calculate_current(self):
        qt = self.quote_type.currentData()
        if qt == "CTO":
            # Disabled in UI; kept for completeness.
            try:
                self._pcp.recalc()
            except Exception:
                pass
            return

        if qt == "ETO":
            tbl, sow, err = self._eto_tbl, self._eto_sow, self._eto_err
        else:
            tbl, sow, err = self._rx_tbl, self._rx_sow, self._rx_err

        sow_text = sow.toPlainText().strip()
        if qt == "REACTIVE" and getattr(self, "_rx_sow_required", False) and not sow_text:
            err.setText("Scope of Work (SOW) is required for Reactive quotes.")
            return

        err.setText("")
        lines = []
        for r in range(tbl.rowCount()):
            resource = (tbl.item(r, 0).text() if tbl.item(r, 0) else "").strip()
            days_s = (tbl.item(r, 1).text() if tbl.item(r, 1) else "0").strip()
            hpd_s = (tbl.item(r, 2).text() if tbl.item(r, 2) else "0").strip()
            rate_key = (tbl.item(r, 3).text() if tbl.item(r, 3) else "").strip()

            try:
                days = float(days_s) if days_s else 0.0
                hours_per_day = float(hpd_s) if hpd_s else 0.0
            except Exception:
                err.setText("Days and Hours/Day must be numeric.")
                return

            if days <= 0:
                continue

            rate, _desc = self.data.get_rate(rate_key)
            hours = days * hours_per_day
            cost = hours * rate
            lines.append({
                "resource": resource,
                "days": days,
                "hours_per_day": hours_per_day,
                "hours": hours,
                "rate_key": rate_key,
                "rate": rate,
                "cost": cost,
            })

        if not lines:
            err.setText("Enter at least one non-zero day value.")
            return

        total = sum(x["cost"] for x in lines)
        self._last_tm = {"quote_type": qt, "sow": sow_text, "lines": lines, "total": total}
        QMessageBox.information(self, "Calculated", f"T&M Total: ${total:,.2f}")

    def print_current(self):
        qt = self.quote_type.currentData()
        if qt == "CTO":
            # Disabled in UI; kept for completeness.
            self._pcp.print_quote_preview()
            return

        if not hasattr(self, "_last_tm"):
            self.calculate_current()
            if not hasattr(self, "_last_tm"):
                return

        data = self._last_tm
        html = build_tm_quote_html(
            quote_type=data["quote_type"],
            sow_text=data["sow"],
            lines=data["lines"],
            total=data["total"],
            logo_path=(ASSETS_DIR / "Pearson Logo.png")
        )
        write_html_temp_and_open(html)
