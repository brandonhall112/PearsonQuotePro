"""Legacy PCP v1.1 window components."""

from __future__ import annotations

import tkinter as tk


class PCPMainWindow(tk.Frame):
    """A self-contained PCP workspace."""

    def __init__(self, parent: tk.Misc, mode_name: str = "CTO") -> None:
        super().__init__(parent, bg="#f2f3f5")
        self.mode_name = mode_name
        self._build_ui()

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg="#1e2a38", height=48)
        header.pack(fill="x")
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="CommissionPro",
            bg="#1e2a38",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
            padx=14,
        )
        title.pack(fill="both", expand=True)

        body = tk.Frame(self, bg="#f2f3f5", padx=18, pady=18)
        body.pack(fill="both", expand=True)

        tk.Label(
            body,
            text="Workspace",
            bg="#f2f3f5",
            fg="#1e2a38",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            body,
            text=(
                "Independent PCPMainWindow instance loaded."
            ),
            bg="#f2f3f5",
            fg="#4b5563",
            font=("Segoe UI", 10),
            anchor="w",
            pady=8,
        ).pack(fill="x")
