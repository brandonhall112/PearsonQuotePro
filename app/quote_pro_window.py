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


def build_pcp_stylesheet() -> str:
    # This mirrors PCP v1.1 "Pearson-ish palette" styling so all tabs share look/feel.
    blue = "#0B2E4B"
    gold = "#F05A28"
    neutral = "#64748B"
    red = "#B91C1C"

    css = """
    QWidget { font-family: Arial, Helvetica, sans-serif; font-size: 10pt; color: #0F172A; }
    QFrame#header { background: __BLUE__; border-bottom: 3px solid __GOLD__; }
    QLabel#title { color: white; font-size: 16pt; font-weight: 700; }
    QLabel#subtitle { color: #E2E8F0; font-size: 9pt; }
    QPushButton {
        background: __GOLD__;
        color: white;
        padding: 10px 14px;
        border-radius: 10px;
        font-weight: 700;
    }
    QPushButton:hover { opacity: 0.9; }
    QPushButton:disabled { background: #CBD5E1; color: #475569; }
    QComboBox {
        padding: 8px 10px;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        background: white;
        min-width: 220px;
    }
    QTextEdit {
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        padding: 8px;
        background: white;
    }
    QTableWidget {
        border: 1px solid #E6E8EB;
        border-radius: 12px;
        background: white;
        gridline-color: #E6E8EB;
    }
    QHeaderView::section {
        background: #F1F5F9;
        border: 0px;
        padding: 8px;
        font-weight: 700;
        color: #0F172A;
    }
    QFrame#panel {
        background: #FFFFFF;
        border: 1px solid #E6E8EB;
        border-radius: 12px;
        padding: 12px;
    }
    QLabel#panelTitle { font-size: 12pt; font-weight: 700; color: __BLUE__; }
    QLabel#hint { color: __NEUTRAL__; }
    QLabel#error { color: __RED__; font-weight: 700; }
    """
    return css.replace("__BLUE__", blue).replace("__GOLD__", gold).replace("__NEUTRAL__", neutral).replace("__RED__", red)


class QuoteProWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1400, 900)
        self.setStyleSheet(build_pcp_stylesheet())

        # Load Excel (shared across quote types)
        self.excel_path = self._resolve_excel()
        self.data = ExcelData(self.excel_path)

        # Header
        header = QFrame()
        header.setObjectName("header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 12, 16, 12)

        title_box = QVBoxLayout()
        title = QLabel(APP_TITLE)
        title.setObjectName("title")
        subtitle = QLabel(f"Config: {self.excel_path.name}")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        hl.addLayout(title_box)
        hl.addStretch(1)

        self.quote_type = QComboBox()
        self.quote_type.addItem("Commissioning (CTO)", "CTO")
        self.quote_type.addItem("Complex Install (ETO)", "ETO")
        self.quote_type.addItem("Reactive (Break/Fix)", "REACTIVE")
        self.quote_type.currentIndexChanged.connect(self._on_quote_type_changed)

        self.btn_calc = QPushButton("Calculate")
        self.btn_calc.clicked.connect(self.calculate_current)

        self.btn_print = QPushButton("Print / Preview")
        self.btn_print.clicked.connect(self.print_current)

        hl.addWidget(self.quote_type)
        hl.addWidget(self.btn_calc)
        hl.addWidget(self.btn_print)

        # Tabs
        self.tabs = QTabWidget()
        self.tab_common = self._build_common_tab()
        self.tab_cto = self._build_cto_tab()
        self.tab_eto = self._build_tm_tab(kind="ETO")
        self.tab_reactive = self._build_tm_tab(kind="REACTIVE", sow_required=True)

        self.tabs.addTab(self.tab_common, "Common")
        self.tabs.addTab(self.tab_cto, "CTO")
        self.tabs.addTab(self.tab_eto, "ETO")
        self.tabs.addTab(self.tab_reactive, "Reactive")

        # Main layout
        root = QWidget()
        vl = QVBoxLayout(root)
        vl.setContentsMargins(12, 12, 12, 12)
        vl.setSpacing(10)
        vl.addWidget(header)
        vl.addWidget(self.tabs)

        self.setCentralWidget(root)

        self._on_quote_type_changed()

    def _resolve_excel(self) -> Path:
        # Use PCP resolver but point it at Quote Pro assets directory
        # PCP resolve_excel_path looks relative to its module file; we want our assets.
        expected = "Tech days and quote rates.xlsx"
        p = ASSETS_DIR / expected
        if p.exists():
            return p
        # fallback to PCP behavior
        rp = resolve_excel_path(expected)
        if rp is None:
            raise FileNotFoundError(f"Could not find {expected} in assets.")
        return rp

    def _build_common_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        panel = QFrame()
        panel.setObjectName("panel")
        pl = QVBoxLayout(panel)

        t = QLabel("Common Info (used for all quote types)")
        t.setObjectName("panelTitle")
        pl.addWidget(t)

        hint = QLabel("This first pass keeps Common lightweight. We’ll wire these fields into CTO + T&M outputs next increment.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        pl.addWidget(hint)

        layout.addWidget(panel)
        layout.addStretch(1)
        return w

    def _build_cto_tab(self) -> QWidget:
        # Embed PCP MainWindow content without modifying PCP logic.
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(0, 0, 0, 0)

        self._pcp = PCPMainWindow()
        # Reuse the already-loaded Excel to avoid double prompts. Replace PCP data with ours.
        self._pcp.data = self.data

        central = self._pcp.takeCentralWidget()  # QWidget
        central.setParent(tab)
        l.addWidget(central)

        return tab

    def _build_tm_tab(self, kind: str, sow_required: bool = False) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        panel = QFrame()
        panel.setObjectName("panel")
        pl = QVBoxLayout(panel)
        title = QLabel("Time & Material")
        title.setObjectName("panelTitle")
        pl.addWidget(title)

        hint = QLabel("Enter days by resource type. Rates come from the shared workbook (Service Rates).")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        pl.addWidget(hint)

        # T&M grid
        tbl = QTableWidget(2, 4)
        tbl.setHorizontalHeaderLabels(["Resource", "Days", "Hours/Day", "Rate Key (from workbook)"])
        tbl.verticalHeader().setVisible(False)
        tbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tbl.setFixedHeight(120)

        # defaults
        hours_per_day = 8 if kind == "ETO" else 10
        # Rate keys used by PCP ExcelData: these are descriptions in Service Rates sheet
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

        # SOW
        sow = QTextEdit()
        sow.setPlaceholderText("Scope of Work (prints above the line item table) ...")
        sow.setFixedHeight(180)

        sow_label = QLabel("Scope of Work (SOW)")
        sow_label.setObjectName("panelTitle")
        sow_label.setStyleSheet("font-size:11pt;")
        pl.addWidget(sow_label)
        pl.addWidget(sow)

        err = QLabel("")
        err.setObjectName("error")
        err.setWordWrap(True)
        pl.addWidget(err)

        layout.addWidget(panel)
        layout.addStretch(1)

        # store references
        if kind == "ETO":
            self._eto_tbl = tbl
            self._eto_sow = sow
            self._eto_err = err
        else:
            self._rx_tbl = tbl
            self._rx_sow = sow
            self._rx_err = err
            self._rx_sow_required = sow_required

        return tab

    def _on_quote_type_changed(self):
        qt = self.quote_type.currentData()
        if qt == "CTO":
            self.tabs.setCurrentWidget(self.tab_cto)
        elif qt == "ETO":
            self.tabs.setCurrentWidget(self.tab_eto)
        else:
            self.tabs.setCurrentWidget(self.tab_reactive)

    def calculate_current(self):
        qt = self.quote_type.currentData()
        if qt == "CTO":
            # PCP computes inside its UI. Trigger its recalc for safety.
            try:
                self._pcp.recalc()
            except Exception:
                pass
            return

        # Validate and compute T&M totals; store a last_result dict for printing.
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
            self._pcp.print_quote_preview()
            return

        # Must calculate first
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
