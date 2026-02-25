import os
import base64
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
import tempfile


def build_tm_quote_html(quote_type: str, sow_text: str, lines: List[Dict[str, float]], total: float, logo_path: Path | None = None) -> str:
    today = date.today()
    validity = today + timedelta(days=30)
    date_str = f"{today:%B} {today.day}, {today:%Y}"
    valid_str = f"{validity:%B} {validity.day}, {validity:%Y}"

    logo_html = ""
    if logo_path and logo_path.exists():
        try:
            b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
            logo_html = f'<img src="data:image/png;base64,{b64}" height="36" style="height:36px;" />'
        except Exception:
            logo_html = ""

    # Match PCP v1.1 look: same general typography and orange rule
    style = """
    <style>
      body { font-family: Arial, Helvetica, sans-serif; font-size: 10pt; color: #0F172A; }
      .topbar { display:flex; align-items:flex-start; justify-content:space-between; border-bottom: 3px solid #F05A28; padding-bottom: 10px; margin-bottom: 14px; }
      .logo { display:flex; align-items:center; gap:10px; }
      .title { font-size: 14pt; font-weight: 700; margin: 0; }
      .meta { font-size: 9pt; color: #475569; }
      .section { margin-top: 12px; }
      .h { font-size: 11pt; font-weight: 700; margin: 0 0 6px 0; color: #0B2E4B; }
      .sow { border: 1px solid #E6E8EB; border-radius: 10px; padding: 10px; background: #FFFFFF; white-space: pre-wrap; }
      table { width:100%; border-collapse: collapse; margin-top: 8px; }
      th, td { border-bottom: 1px solid #E6E8EB; padding: 8px; text-align:left; vertical-align: top; }
      th { background: #F1F5F9; font-weight: 700; }
      .right { text-align:right; }
      .total { font-size: 12pt; font-weight: 700; }
      .foot { margin-top: 16px; font-size: 9pt; color: #475569; }
    </style>
    """

    # SOW is above line items (per your instruction)
    sow_block = sow_text.strip() if sow_text else ""

    rows = []
    for x in lines:
        rows.append(f"""
          <tr>
            <td>{x['resource']}</td>
            <td class="right">{x['days']:.2f}</td>
            <td class="right">{x['hours_per_day']:.2f}</td>
            <td class="right">{x['hours']:.2f}</td>
            <td>{x['rate_key']}</td>
            <td class="right">${x['rate']:,.2f}</td>
            <td class="right">${x['cost']:,.2f}</td>
          </tr>
        """)

    body = f"""
    <html><head>{style}</head><body>
      <div class="topbar">
        <div class="logo">
          {logo_html}
          <div>
            <p class="title">Pearson Quote Pro — {quote_type}</p>
            <div class="meta">Quote Date: {date_str} &nbsp;|&nbsp; Valid Through: {valid_str}</div>
          </div>
        </div>
        <div class="meta" style="text-align:right;">
          Time & Material Quote
        </div>
      </div>

      <div class="section">
        <div class="h">Scope of Work</div>
        <div class="sow">{sow_block if sow_block else "—"}</div>
      </div>

      <div class="section">
        <div class="h">Line Items</div>
        <table>
          <thead>
            <tr>
              <th>Resource</th>
              <th class="right">Days</th>
              <th class="right">Hours/Day</th>
              <th class="right">Hours</th>
              <th>Rate Key</th>
              <th class="right">Rate</th>
              <th class="right">Ext.</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
          <tfoot>
            <tr>
              <td colspan="6" class="right total">Total</td>
              <td class="right total">${total:,.2f}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div class="foot">
        Notes: This is a first-pass Time & Material format. Assumptions/exclusions blocks will be pulled from Excel in the next increment.
      </div>
    </body></html>
    """
    return body


def write_html_temp_and_open(html: str) -> None:
    fd, path = tempfile.mkstemp(suffix=".html", prefix="pearson_quote_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html)
    QDesktopServices.openUrl(QUrl.fromLocalFile(path))
