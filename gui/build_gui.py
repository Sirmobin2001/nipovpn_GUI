"""Build the NipoVPN GUI into a distributable desktop bundle.

Usage:

    python build_gui.py --onedir
    python build_gui.py --onefile
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _default_icon_path() -> Path | None:
    for candidate in (Path("assets/app.ico"), Path("assets/app.png")):
        if candidate.is_file():
            return candidate
    return None


def _add_data_arg(source: Path, destination: str) -> str:
    return f"{source}{os.pathsep}{destination}"


def build() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--onefile", action="store_true", help="Create a single file bundle")
    group.add_argument("--onedir", action="store_true", help="Create a directory bundle")
    parser.add_argument(
        "--core",
        type=Path,
        help="Optional path to the nipovpn core binary to bundle next to the GUI",
    )
    parser.add_argument(
        "--icon",
        type=Path,
        help="Optional path to an app icon file",
    )
    parser.add_argument(
        "--distpath",
        type=Path,
        default=Path("dist"),
        help="PyInstaller output directory",
    )
    args = parser.parse_args()

    pyinstaller = shutil.which("pyinstaller")
    if pyinstaller is None:
        print("PyInstaller is not installed. Run `pip install -r requirements-dev.txt` first.")
        return 1

    command = [
        pyinstaller,
        "--noconfirm",
        "--clean",
        "--name",
        "nipovpn-gui",
        "--windowed",
        "--distpath",
        str(args.distpath),
        "--workpath",
        "build",
    ]
    if args.onefile or not args.onedir:
        command.append("--onefile")
    else:
        command.append("--onedir")

    icon_path = args.icon or _default_icon_path()
    if icon_path is not None:
        command.extend(["--icon", str(icon_path)])
        command.extend(["--add-data", _add_data_arg(icon_path, "assets")])

    if args.core:
        command.extend(["--add-binary", f"{args.core}{os.pathsep}."])

    command.append("main.py")

    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(build())
