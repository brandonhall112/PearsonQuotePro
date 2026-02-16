import sys
from PySide6.QtWidgets import QApplication
from app.multi_mode_window import MultiModeWindow


def main() -> int:
    app = QApplication(sys.argv)
    w = MultiModeWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
