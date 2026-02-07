from __future__ import annotations

from dataclasses import dataclass
from typing import List

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QSizePolicy
)

from legacy_pcp.pcp_v1_1 import MainWindow as PCPMainWindow


DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@dataclass
class ResourceRow:
    role: str          # "Technician" or "Engineer"
    start_day: str     # "Mon".."Sun"
    onsite_days: int


class ReactiveResourceModel(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.rows: List[ResourceRow] = []

    def set_counts(self, techs: int, engs: int):
        rows: List[ResourceRow] = []
        for i in range(techs):
            rows.append(ResourceRow(role=f"Technician {i+1}", start_day="Mon", onsite_days=1))
        for i in range(engs):
            rows.append(ResourceRow(role=f"Engineer {i+1}", start_day="Mon", onsite_days=1))
        self.rows = rows
        self.changed.emit()


class ReactiveResourcesPanel(QFrame):
    """
    Drop-in replacement for PCP's Machine Configuration inputs on the Reactive tab.

    Requirements:
    - User selects number of techs and engineers
    - Each resource has:
        - first onsite day (day of week)
        - number of days onsite from that start day
    - Reactive is always quoted as 10-hour days (we surface this as a banner + property)
    """
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("softBox")  # matches PCP styling for boxed sections
        self.model = ReactiveResourceModel()
        self.model.changed.connect(self._render_rows)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        banner = QLabel("Reactive quotes assume 10-hour days (fixed).")
        banner.setWordWrap(True)
        banner.setStyleSheet("font-weight: 700;")
        root.addWidget(banner)

        # Counts row
        counts = QFrame()
        cl = QHBoxLayout(counts)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(10)

        cl.addWidget(QLabel("Technicians"))
        self.spin_techs = QSpinBox()
        self.spin_techs.setRange(0, 20)
        self.spin_techs.setValue(1)
        self.spin_techs.valueChanged.connect(self._counts_changed)
        cl.addWidget(self.spin_techs)

        cl.addSpacing(16)

        cl.addWidget(QLabel("Engineers"))
        self.spin_engs = QSpinBox()
        self.spin_engs.setRange(0, 20)
        self.spin_engs.setValue(0)
        self.spin_engs.valueChanged.connect(self._counts_changed)
        cl.addWidget(self.spin_engs)

        cl.addStretch(1)
        root.addWidget(counts)

        # Resource table
        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(["Resource", "First Onsite Day", "Onsite Days"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tbl.setFixedHeight(220)
        root.addWidget(self.tbl)

        # Seed
        self.model.set_counts(self.spin_techs.value(), self.spin_engs.value())

    def _counts_changed(self):
        self.model.set_counts(self.spin_techs.value(), self.spin_engs.value())

    def _render_rows(self):
        self.tbl.setRowCount(len(self.model.rows))
        for r, row in enumerate(self.model.rows):
            # Resource (read-only label)
            item = QTableWidgetItem(row.role)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.tbl.setItem(r, 0, item)

            # Start day combo
            cb = QComboBox()
            cb.addItems(DAYS)
            cb.setCurrentText(row.start_day)
            cb.currentTextChanged.connect(lambda v, rr=r: self._set_start_day(rr, v))
            self.tbl.setCellWidget(r, 1, cb)

            # Onsite days spin
            sp = QSpinBox()
            sp.setRange(1, 60)
            sp.setValue(row.onsite_days)
            sp.valueChanged.connect(lambda v, rr=r: self._set_onsite_days(rr, int(v)))
            self.tbl.setCellWidget(r, 2, sp)

    def _set_start_day(self, idx: int, day: str):
        if 0 <= idx < len(self.model.rows):
            self.model.rows[idx].start_day = day
            self.model.changed.emit()

    def _set_onsite_days(self, idx: int, days: int):
        if 0 <= idx < len(self.model.rows):
            self.model.rows[idx].onsite_days = days
            self.model.changed.emit()

    def get_resources(self) -> List[ResourceRow]:
        return list(self.model.rows)


class ReactiveMainWindow(PCPMainWindow):
    """
    PCP MainWindow with the Machine Configuration section repurposed for Reactive inputs.
    We keep overall PCP look/feel; we only surgically hide machine-specific widgets and insert
    the ReactiveResourcesPanel in that same left-side area.

    NOTE: This is step 1: inputs only. Calculation/outputs will be adapted in later increments.
    """
    reactive_hours_per_day = 10  # fixed for Reactive

    def __init__(self):
        super().__init__()
        self._apply_reactive_ui_patch()

    def _apply_reactive_ui_patch(self):
        # 1) Hide "Customer Install Window" control (spin_window parent container)
        if hasattr(self, "spin_window") and self.spin_window is not None:
            p = self.spin_window.parent()
            if isinstance(p, QWidget):
                p.setVisible(False)

        # 2) Hide machine lines scroll + add-machine button + machine-specific note
        if hasattr(self, "scroll") and self.scroll is not None:
            self.scroll.setVisible(False)

        add_btn = self.findChild(QWidget, "addMachine")
        if add_btn is not None:
            add_btn.setVisible(False)

        note = self.findChild(QWidget, "note")
        if note is not None:
            note.setVisible(False)

        # 3) Insert our Reactive inputs panel into the left layout, right where the install window box was.
        # We look for the "Machine Configuration" title label by objectName + text.
        panel_title = None
        for w in self.findChildren(QLabel):
            if w.objectName() == "panelTitle" and w.text().strip() == "Machine Configuration":
                panel_title = w
                break

        # The title label was added to left_l; its parent widget should have a QVBoxLayout (left_l).
        if panel_title is None:
            return  # fail-safe; do nothing if PCP UI changes

        left_container = panel_title.parentWidget()
        if left_container is None or left_container.layout() is None:
            return

        left_layout = left_container.layout()

        # Find a good insertion index: after the descriptive QLabel block (typically index 1-2)
        insert_at = 1
        for i in range(left_layout.count()):
            item = left_layout.itemAt(i)
            ww = item.widget() if item else None
            if isinstance(ww, QLabel) and "Add machines to estimate" in ww.text():
                insert_at = i + 1
                break

        self.reactive_panel = ReactiveResourcesPanel()
        left_layout.insertWidget(insert_at, self.reactive_panel)

        # 4) Optional: tweak the help text under the title to match reactive context (inputs only).
        for w in self.findChildren(QLabel):
            if "Add machines to estimate commissioning requirements" in w.text():
                w.setText(
                    "Define onsite resources for a reactive service visit.\n"
                    "You will select techs/engineers, their first onsite day, and the number of onsite days."
                )
                break
