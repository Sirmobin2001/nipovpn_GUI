"""Application entry point for the NipoVPN GUI client."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .main_window import MainWindow
from .theme import STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("NipoVPN Client")
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
