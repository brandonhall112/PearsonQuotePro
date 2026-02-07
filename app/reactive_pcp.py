from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QComboBox, QSpinBox, QPushButton, QSizePolicy
)

from legacy_pcp.pcp_v1_1 import MainWindow as PCPMainWindow


DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ResourceType = Literal["Technician", "Engineer"]


@dataclass
class ResourceSelection:
    resource_type: ResourceType
    start_day: str
    onsite_days: int


class ResourceLine(QFrame):
    """
    Reactive equivalent of PCP MachineLine.

    Keeps PCP styling by reusing:
      - QFrame class
      - objectName("machineLine")
      - same padding/spacing
    """
    def __init__(self, on_change, on_delete):
        super().__init__()
        self.on_change = on_change
        self.on_delete = on_delete

        self.setObjectName("machineLine")
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 10, 10, 10)
        row.setSpacing(10)

        self.cmb_type = QComboBox()
        self.cmb_type.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_type.addItems(["Technician", "Engineer"])
        self.cmb_type.currentIndexChanged.connect(self._changed)

        self.cmb_start = QComboBox()
        self.cmb_start.addItems(DAYS)
        self.cmb_start.currentIndexChanged.connect(self._changed)

        self.spin_days = QSpinBox()
        self.spin_days.setRange(1, 60)
        self.spin_days.setValue(1)
        self.spin_days.valueChanged.connect(self._changed)

        self.btn_delete = QPushButton("🗑")
        self.btn_delete.setFixedWidth(40)
        self.btn_delete.clicked.connect(self._delete)

        row.addWidget(QLabel("Resource"))
        row.addWidget(self.cmb_type, 2)
        row.addWidget(QLabel("Start"))
        row.addWidget(self.cmb_start)
        row.addWidget(QLabel("Onsite Days"))
        row.addWidget(self.spin_days)
        row.addWidget(self.btn_delete)

    def _changed(self, *_):
        self.on_change()

    def _delete(self):
        self.on_delete(self)

    def value(self) -> ResourceSelection:
        return ResourceSelection(
            resource_type=self.cmb_type.currentText(),  # type: ignore
            start_day=self.cmb_start.currentText(),
            onsite_days=int(self.spin_days.value()),
        )


class ReactiveMainWindow(PCPMainWindow):
    """
    PCP MainWindow adapted for Reactive quoting inputs by repurposing Machine Configuration.

    Changes (Reactive tab only):
    - "+ Add Machine" -> "+ Add Resource"
    - MachineLine rows replaced with ResourceLine rows:
        Resource Type (Tech/Engineer), Start Day (Mon..Sun), Onsite Days
    - Customer Install Window selection hidden
    - Training note hidden (not applicable)

    For now:
    - We do NOT run PCP commissioning math. We compute and display basic totals in the cards only.
    - Reactive day length is fixed at 10 hours/day (used later in pricing math).
    """
    reactive_hours_per_day = 10

    def __init__(self):
        super().__init__()
        self._apply_reactive_ui_patch()

    def _apply_reactive_ui_patch(self):
        # Hide customer install window selection (keep widget alive, just hidden)
        if hasattr(self, "spin_window") and self.spin_window is not None:
            p = self.spin_window.parent()
            if isinstance(p, QFrame):
                p.setVisible(False)
            elif p is not None and hasattr(p, "setVisible"):
                p.setVisible(False)

        # Change add button label
        btn_add = self.findChild(QPushButton, "addMachine")
        if btn_add is not None:
            btn_add.setText("+  Add Resource")
            # Disconnect existing handler to PCP add_line, then connect to our add_resource_line
            try:
                btn_add.clicked.disconnect()
            except Exception:
                pass
            btn_add.clicked.connect(self.add_line)  # we override add_line below

        # Update empty hint text
        if hasattr(self, "empty_hint") and self.empty_hint is not None:
            self.empty_hint.setText("No resources added.\nClick “Add Resource” to begin.")

        # Hide training note (no longer relevant)
        note = self.findChild(QLabel, "note")
        if note is not None:
            note.setVisible(False)

        # Update the helper text under "Machine Configuration" if present
        for w in self.findChildren(QLabel):
            if "Add machines to estimate commissioning requirements" in w.text():
                w.setText(
                    "Add onsite resources for a reactive service visit.\n"
                    "Each line is a resource with a start day and total onsite days."
                )
                break

        # If there are already default machine lines, clear them
        try:
            for ln in list(getattr(self, "lines", [])):
                self.delete_line(ln)
        except Exception:
            pass

        # Start with one technician line to match PCP behavior
        self.add_line()

        # Hide workload chart will stay for now; later replaced with calendar view.

    # --- Override PCP machine-line handlers ---

    def add_line(self):  # overrides PCP add_line
        if getattr(self, "empty_hint", None) is not None:
            self.empty_hint.hide()

        ln = ResourceLine(on_change=self.recalc, on_delete=self.delete_line)
        self.lines.append(ln)
        self.lines_layout.addWidget(ln)
        self.recalc()

    def delete_line(self, ln):  # accept ResourceLine
        try:
            self.lines.remove(ln)
        except Exception:
            pass
        ln.setParent(None)
        ln.deleteLater()

        if len(self.lines) == 0:
            if getattr(self, "empty_hint", None) is not None:
                self.empty_hint.show()
            self._reset_reactive_views()
        else:
            self.recalc()

    # --- Reactive recalc (inputs only, no pricing yet) ---

    def recalc(self, *_):  # override PCP recalc to avoid commissioning logic
        tech_count = 0
        eng_count = 0
        tech_days = 0
        eng_days = 0

        for ln in getattr(self, "lines", []):
            if not hasattr(ln, "value"):
                continue
            v = ln.value()
            if v.resource_type == "Technician":
                tech_count += 1
                tech_days += int(v.onsite_days)
            else:
                eng_count += 1
                eng_days += int(v.onsite_days)

        # Update PCP cards (keep the same UI components)
        if hasattr(self, "card_tech"):
            self.card_tech.set_value(str(tech_count), f"{tech_days} total days")
        if hasattr(self, "card_eng"):
            self.card_eng.set_value(str(eng_count), f"{eng_days} total days")

        # Hide / neutralize install window card
        if hasattr(self, "card_window"):
            self.card_window.set_value("—", "Reactive uses 10-hr days")

        # Keep totals elsewhere at zero for now; we’ll wire pricing/output later.
        # The rest of the PCP UI will still display, but this prevents crashes.

    def _reset_reactive_views(self):
        if hasattr(self, "card_tech"):
            self.card_tech.set_value("0", "0 total days")
        if hasattr(self, "card_eng"):
            self.card_eng.set_value("0", "0 total days")
        if hasattr(self, "card_window"):
            self.card_window.set_value("—", "Reactive uses 10-hr days")
