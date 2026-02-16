"""Application entrypoint for Pearson Quote Pro."""

from app.multi_mode_window import MultiModeWindow


def main() -> None:
    app = MultiModeWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
