"""Application entry point for the NipoVPN GUI client."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow
from .theme import STYLESHEET
from .utils import bundled_icon_path


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--icon", type=Path, help="Path to a custom app icon")
    args, remaining = parser.parse_known_args(sys.argv[1:])

    app = QApplication([sys.argv[0], *remaining])
    app.setApplicationName("NipoVPN Client")
    app.setStyleSheet(STYLESHEET)

    icon_path = str(args.icon) if args.icon and args.icon.is_file() else bundled_icon_path()
    if icon_path:
        icon = QIcon(icon_path)
        app.setWindowIcon(icon)

    window = MainWindow()
    if icon_path:
        window.setWindowIcon(QIcon(icon_path))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
