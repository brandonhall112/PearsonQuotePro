"""Multi-mode host window for Quote Pro."""

from __future__ import annotations

import tkinter as tk

from app.pcp_factory import get_pcp_main_window_class


class MultiModeWindow(tk.Tk):
    """Single app window with top mode buttons and stacked PCP workspaces."""

    MODES = ("CTO", "ETO", "Ractive")

    def __init__(self) -> None:
        super().__init__()
        self.title("Pearson Quote Pro")
        self.geometry("1180x760")
        self.configure(bg="#d7dce2")

        self._mode_buttons: dict[str, tk.Button] = {}
        self._mode_windows: dict[str, tk.Widget] = {}

        self._build_ui()
        self.show_mode("CTO")

    def _build_ui(self) -> None:
        top_bar = tk.Frame(self, bg="#1e2a38", padx=10, pady=8)
        top_bar.pack(fill="x")

        for mode in self.MODES:
            button = tk.Button(
                top_bar,
                text=mode,
                command=lambda mode_name=mode: self.show_mode(mode_name),
                relief="flat",
                bg="#2d3f53",
                fg="white",
                activebackground="#415c77",
                activeforeground="white",
                font=("Segoe UI", 10, "bold"),
                padx=16,
                pady=6,
            )
            button.pack(side="left", padx=(0, 8))
            self._mode_buttons[mode] = button

        host = tk.Frame(self, bg="#d7dce2")
        host.pack(fill="both", expand=True)

        pcp_main_window_class = get_pcp_main_window_class()
        for mode in self.MODES:
            mode_window = pcp_main_window_class(host)
            mode_window.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._mode_windows[mode] = mode_window

    def show_mode(self, mode: str) -> None:
        if mode not in self._mode_windows:
            return

        self._mode_windows[mode].lift()

        for mode_name, button in self._mode_buttons.items():
            if mode_name == mode:
                button.configure(bg="#5f7ea0")
            else:
                button.configure(bg="#2d3f53")
