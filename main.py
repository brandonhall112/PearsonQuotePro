import sys
from PySide6.QtWidgets import QApplication
from app.quote_pro_window import QuoteProWindow


def main() -> int:
    app = QApplication(sys.argv)
    w = QuoteProWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
