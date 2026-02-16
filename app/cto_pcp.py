from __future__ import annotations

import base64
from datetime import date, timedelta
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from legacy_pcp.pcp_v1_1 import MainWindow as PCPMainWindow
from legacy_pcp.pcp_v1_1 import RoleTotals, ExpenseLine, Assignment, money, LOGO_PATH, TRAVEL_DAYS_PER_PERSON, Section


class CTOMainWindow(PCPMainWindow):
    """CTO-specific behavior ported into Quote Pro without affecting ETO/Reactive tabs."""

    def __init__(self):
        super().__init__()
        self._build_cto_header_form()
        self._build_workload_calendar_ui()
        self._apply_cto_table_formatting()

    def _build_cto_header_form(self):
        form_section = Section("Quote Header", "Information shown at the top of the printed quote.", "🧾")
        form = QFrame()
        lay = QVBoxLayout(form)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.quote_fields: dict[str, QLineEdit] = {}
        for label in ["Customer Name", "Reference", "Submitted to", "Prepared By"]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setMinimumWidth(120)
            inp = QLineEdit()
            inp.setPlaceholderText(label)
            row.addWidget(lbl)
            row.addWidget(inp, 1)
            lay.addLayout(row)
            self.quote_fields[label] = inp

        form_section.content_layout.addWidget(form)
        self.right_content.layout().insertWidget(0, form_section)

    def _build_workload_calendar_ui(self):
        # Hide legacy chart-centric workload section for CTO and replace with a 14-day calendar.
        if hasattr(self, "chart_view") and self.chart_view is not None:
            self.chart_view.setVisible(False)

        sec = Section("Workload Calendar (14-Day)", "Travel and onsite schedule by assigned resource.", "🗓")

        legend = QHBoxLayout()
        legend.addWidget(QLabel("Legend:"))
        legend.addWidget(self._legend_chip("Travel", "#d9e8ff"))
        legend.addWidget(self._legend_chip("Onsite", "#d7f4df"))
        legend.addStretch(1)
        sec.content_layout.addLayout(legend)

        headers = ["Resource", "Group"] + [f"D{i}" for i in range(1, 15)]
        self.tbl_calendar = QTableWidget(0, len(headers))
        self.tbl_calendar.setHorizontalHeaderLabels(headers)
        self.tbl_calendar.verticalHeader().setVisible(False)
        self.tbl_calendar.setAlternatingRowColors(True)
        sec.content_layout.addWidget(self.tbl_calendar)

        self.right_content.layout().insertWidget(1, sec)

    def _legend_chip(self, text: str, color: str) -> QFrame:
        f = QFrame()
        r = QHBoxLayout(f)
        r.setContentsMargins(0, 0, 0, 0)
        sw = QLabel("  ")
        sw.setStyleSheet(f"background:{color}; border:1px solid #9aa4b2; min-width:16px; max-width:16px;")
        r.addWidget(sw)
        r.addWidget(QLabel(text))
        return f

    @staticmethod
    def _is_rpc(model: str) -> bool:
        return str(model).strip().upper().startswith("RPC")

    def _apply_cto_table_formatting(self):
        # Consistent widths across CTO tables + right-aligned monetary headers.
        stretch_indices = {
            self.tbl_breakdown: [0, 2, 3],
            self.tbl_labor: [0, 1],
            self.tbl_exp: [0, 1],
            self.tbl_calendar: [0, 1],
        }
        for tbl, stretch_cols in stretch_indices.items():
            hdr = tbl.horizontalHeader()
            for c in range(tbl.columnCount()):
                mode = hdr.ResizeMode.Stretch if c in stretch_cols else hdr.ResizeMode.ResizeToContents
                hdr.setSectionResizeMode(c, mode)

        # Right align monetary headers
        self.tbl_labor.horizontalHeaderItem(4).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tbl_exp.horizontalHeaderItem(2).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def calc(self):
        tech, eng, exp_lines, meta = super().calc()

        # Group/isolated ordering for RPC models.
        meta["machine_rows"] = sorted(meta["machine_rows"], key=lambda r: (0 if not self._is_rpc(r["model"]) else 1, r["model"]))
        meta["assignments"] = sorted(meta["assignments"], key=lambda a: (0 if not self._is_rpc(a.model) else 1, a.model, a.role, a.person_num))
        return tech, eng, exp_lines, meta

    def _render_calendar(self, assignments: List[Assignment]):
        self.tbl_calendar.setRowCount(len(assignments))

        travel_color = QColor("#d9e8ff")
        onsite_color = QColor("#d7f4df")

        for r, a in enumerate(assignments):
            label = f"{a.role[:1]}{a.person_num} - {a.model}"
            group = "RPC" if self._is_rpc(a.model) else "Non-RPC"
            self.tbl_calendar.setItem(r, 0, QTableWidgetItem(label))
            self.tbl_calendar.setItem(r, 1, QTableWidgetItem(group))

            travel_in = 1 if (a.role == "Engineer" and a.model in {"RPC-PH", "RPC-OU"}) else 0
            onsite_start = travel_in + 1
            onsite_end = min(onsite_start + int(a.onsite_days) - 1, 12)
            travel_out = onsite_end + 1

            for d in range(14):
                cell = QTableWidgetItem("")
                if d == travel_in or d == travel_out:
                    cell.setBackground(travel_color)
                    cell.setText("T")
                elif onsite_start <= d <= onsite_end:
                    cell.setBackground(onsite_color)
                    cell.setText("O")
                cell.setTextAlignment(Qt.AlignCenter)
                self.tbl_calendar.setItem(r, d + 2, cell)

    def recalc(self):
        super().recalc()
        try:
            self._apply_cto_table_formatting()
            assigns = self.calc()[3]["assignments"]
            self._render_calendar(assigns)
        except Exception:
            pass

    def build_quote_html(self, tech: RoleTotals, eng: RoleTotals, exp_lines: List[ExpenseLine], meta: dict) -> str:
        today = date.today()
        validity = today + timedelta(days=30)
        date_str = f"{today:%B} {today.day}, {today:%Y}"
        valid_str = f"{validity:%B} {validity.day}, {validity:%Y}"

        logo_html = ""
        if LOGO_PATH.exists():
            try:
                logo_html = f'<img src="data:image/png;base64,{base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")}" height="36" />'
            except Exception:
                logo_html = ""

        machine_rows = []
        for r in meta["machine_rows"]:
            machine_rows.append(
                f"<tr><td>{r['model']}</td><td style='text-align:center'>{r['qty']}</td>"
                f"<td>{r['tech_total']}</td><td style='text-align:center'>{r['eng_total'] if r['eng_total'] else '—'}</td>"
                f"<td style='text-align:center'>{r['tech_headcount'] if r['tech_headcount'] else '—'}</td>"
                f"<td style='text-align:center'>{r['eng_headcount'] if r['eng_headcount'] else '—'}</td></tr>"
            )

        labor_sub = tech.labor_cost + eng.labor_cost
        exp_rows = "".join(
            [f"<tr><td>{e.description}</td><td>{e.details}</td><td class='right'>{money(e.extended)}</td></tr>" for e in exp_lines]
        )

        req_html = ""
        if self.data.requirements:
            req_html = "<h3>Requirements & Assumptions</h3><ul>" + "".join([f"<li>{x}</li>" for x in self.data.requirements]) + "</ul>"

        # Print calendar with legend
        cal_rows = []
        for a in meta["assignments"]:
            travel_in = 1 if (a.role == "Engineer" and a.model in {"RPC-PH", "RPC-OU"}) else 0
            onsite_start = travel_in + 1
            onsite_end = min(onsite_start + int(a.onsite_days) - 1, 12)
            travel_out = onsite_end + 1
            row_cells = []
            for d in range(14):
                cls = ""
                txt = ""
                if d == travel_in or d == travel_out:
                    cls, txt = "travel", "T"
                elif onsite_start <= d <= onsite_end:
                    cls, txt = "onsite", "O"
                row_cells.append(f"<td class='{cls}'>{txt}</td>")
            group = "RPC" if self._is_rpc(a.model) else "Non-RPC"
            cal_rows.append(f"<tr><td>{a.role[:1]}{a.person_num}-{a.model}</td><td>{group}</td>{''.join(row_cells)}</tr>")

        q = lambda key: self.quote_fields[key].text().strip() or "—"

        return f"""<html><head><meta charset='utf-8'/><style>
            body {{ font-family: Arial, Helvetica, sans-serif; font-size:10pt; color:#0F172A; }}
            .topbar {{ display:flex; justify-content:space-between; border-bottom:3px solid #F05A28; padding-bottom:10px; margin-bottom:14px; }}
            .band {{ width:100%; background:#eaf0f4; padding:10px; margin:10px 0 14px 0; box-sizing:border-box; }}
            .two {{ display:table; width:100%; }} .two > div {{ display:table-cell; width:50%; vertical-align:top; padding-right:10px; }}
            .grid {{ width:100%; border-collapse:collapse; margin-top:10px; table-layout:fixed; }}
            .grid th {{ background:#343551; color:white; text-align:left; padding:8px; }} .grid td {{ padding:7px; border-bottom:1px solid #E2E8F0; }}
            .right {{ text-align:right; }} h3 {{ color:#4c4b4c; margin:16px 0 8px 0; }}
            .travel {{ background:#d9e8ff; text-align:center; }} .onsite {{ background:#d7f4df; text-align:center; }}
            .legend span {{ display:inline-block; padding:2px 8px; margin-right:8px; border:1px solid #9aa4b2; }}
        </style></head><body>
        <div class='topbar'><div><p style='margin:0;font-size:18pt;font-weight:800;color:#4c4b4c;'>Commissioning Budget Quote</p><p style='margin:4px 0 0 0;color:#6D6E71;'>Service Estimate</p></div><div>{logo_html}</div></div>

        <table class='grid'><tr><th>Customer Name</th><th>Reference</th><th>Submitted to</th><th>Prepared By</th></tr>
        <tr><td>{q('Customer Name')}</td><td>{q('Reference')}</td><td>{q('Submitted to')}</td><td>{q('Prepared By')}</td></tr></table>

        <div class='band'><div class='two'><div><b>DATE</b><br/>{date_str}<br/><br/><b>TOTAL PERSONNEL</b><br/>{tech.headcount + eng.headcount} ({tech.headcount} Tech, {eng.headcount} Eng)</div>
        <div><b>QUOTE VALIDITY</b><br/>{valid_str}<br/><br/><b>ESTIMATED DURATION</b><br/>{meta['max_onsite']} days onsite + {TRAVEL_DAYS_PER_PERSON} travel days</div></div></div>

        <h3>Workload Calendar (14-Day)</h3>
        <div class='legend'><span class='travel'>Travel (T)</span><span class='onsite'>Onsite (O)</span></div>
        <table class='grid'><tr><th style='width:18%'>Resource</th><th style='width:8%'>Group</th>{''.join([f'<th>D{i}</th>' for i in range(1,15)])}</tr>{''.join(cal_rows)}</table>

        <h3>Machine Breakdown</h3><table class='grid'><tr><th style='width:26%'>Model</th><th style='width:8%;text-align:center;'>Qty</th><th style='width:22%'>Tech Days</th><th style='width:12%;text-align:center;'>Eng Days</th><th style='width:16%;text-align:center;'>Technicians</th><th style='width:16%;text-align:center;'>Engineers</th></tr>{''.join(machine_rows)}</table>

        <h3>Labor Costs</h3><table class='grid'><tr><th style='width:78%'>Item</th><th class='right' style='width:22%'>Extended</th></tr>
        <tr><td>Tech. Regular Time ({tech.total_onsite_days} days × {money(tech.day_rate)}/day)</td><td class='right'>{money(tech.labor_cost)}</td></tr>
        <tr><td>Eng. Regular Time ({eng.total_onsite_days} days × {money(eng.day_rate)}/day)</td><td class='right'>{money(eng.labor_cost)}</td></tr>
        <tr><td><b>Labor Subtotal</b></td><td class='right'><b>{money(labor_sub)}</b></td></tr></table>

        <h3>Estimated Expenses</h3><table class='grid'><tr><th style='width:28%'>Expense</th><th style='width:52%'>Details</th><th class='right' style='width:20%'>Amount</th></tr>{exp_rows}
        <tr><td><b>Expenses Subtotal</b></td><td>—</td><td class='right'><b>{money(meta['exp_total'])}</b></td></tr></table>

        <h3>Estimated Total</h3><div style='background:#eaf0f4;padding:10px;'><b style='font-size:16pt'>{money(meta['grand_total'])}</b></div>
        {req_html}
        </body></html>"""
